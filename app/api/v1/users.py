from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from sqlite3 import Error
from .database import get_db

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all users with pagination"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM users")
        total_records = cursor.fetchone()[0]
        
        # Get users with pagination
        offset = (page - 1) * limit
        cursor.execute("""
            SELECT 
                u.*,
                COUNT(DISTINCT o.opportunity_id) as opportunity_count,
                SUM(CASE WHEN o.is_closed = 0 THEN o.total_amount ELSE 0 END) as open_opportunity_value,
                SUM(CASE WHEN o.is_closed = 1 AND o.is_won = 1 THEN o.total_amount ELSE 0 END) as won_opportunity_value
            FROM users u
            LEFT JOIN opportunities o ON u.user_id = o.owner_id
            GROUP BY u.user_id, u.username, u.first_name, u.last_name, u.full_name, u.created_at
            ORDER BY u.full_name
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        users = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": users
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{user_id}/opportunities")
async def get_user_opportunities(
    user_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_closed: Optional[bool] = None
):
    """Get all opportunities for a specific user"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build query
        query = """
            SELECT 
                o.*,
                a.account_name,
                s.stage_name as current_stage_name,
                ps.source_name,
                o.blockers,
                o.support_needed,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.account_id
            LEFT JOIN stages s ON o.stage_id = s.stage_id
            LEFT JOIN pipeline_sources ps ON o.source_id = ps.source_id
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            WHERE o.owner_id = ?
        """
        params = [user_id]
        
        if is_closed is not None:
            query += " AND o.is_closed = ?"
            params.append(1 if is_closed else 0)
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                o.*,\n                a.account_name,\n                s.stage_name as current_stage_name,\n                ps.source_name,\n                o.blockers,\n                o.support_needed",
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY o.created_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        cursor.execute(query, params)
        opportunities = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": opportunities
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 