from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional
import sqlite3
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/influencer-engagements", tags=["Influencer Engagements"])

class EngagementBase(BaseModel):
    influencer_id: int
    opportunity_id: Optional[int] = None
    engagement_date: datetime
    engagement_type: str
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    created_by: int

class EngagementCreate(EngagementBase):
    pass

class EngagementUpdate(BaseModel):
    engagement_type: Optional[str] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None

def get_db():
    conn = sqlite3.connect('sales_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.get("")
async def list_engagements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    influencer_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    engagement_type: Optional[str] = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Base query
        query = """
            SELECT 
                e.*,
                i.first_name || ' ' || i.last_name as influencer_name,
                o.opportunity_name,
                u.full_name as created_by_name
            FROM influencer_engagements e
            LEFT JOIN influencers i ON e.influencer_id = i.influencer_id
            LEFT JOIN opportunities o ON e.opportunity_id = o.opportunity_id
            LEFT JOIN users u ON e.created_by = u.user_id
            WHERE 1=1
        """
        params = []
        
        if influencer_id:
            query += " AND e.influencer_id = ?"
            params.append(influencer_id)
        
        if opportunity_id:
            query += " AND e.opportunity_id = ?"
            params.append(opportunity_id)
        
        if start_date:
            query += " AND e.engagement_date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND e.engagement_date <= ?"
            params.append(end_date.isoformat())
        
        if engagement_type:
            query += " AND e.engagement_type = ?"
            params.append(engagement_type)
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                e.*,\n                i.first_name || ' ' || i.last_name as influencer_name,\n                o.opportunity_name,\n                u.full_name as created_by_name", 
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Add sorting and pagination
        query += " ORDER BY e.engagement_date DESC"
        offset = (page - 1) * limit
        query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, params)
        engagements = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": engagements
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{engagement_id}")
async def get_engagement(engagement_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                e.*,
                i.first_name || ' ' || i.last_name as influencer_name,
                i.title as influencer_title,
                i.email as influencer_email,
                o.opportunity_name,
                o.total_amount as opportunity_amount,
                o.stage_name as opportunity_stage,
                u.full_name as created_by_name
            FROM influencer_engagements e
            LEFT JOIN influencers i ON e.influencer_id = i.influencer_id
            LEFT JOIN opportunities o ON e.opportunity_id = o.opportunity_id
            LEFT JOIN users u ON e.created_by = u.user_id
            WHERE e.engagement_id = ?
        """, (engagement_id,))
        
        engagement = cursor.fetchone()
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        return dict(engagement)
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("")
async def create_engagement(engagement: EngagementCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate influencer exists
        cursor.execute("SELECT influencer_id FROM influencers WHERE influencer_id = ?", 
                      (engagement.influencer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Validate opportunity if provided
        if engagement.opportunity_id:
            cursor.execute("""
                SELECT opportunity_id 
                FROM opportunities 
                WHERE opportunity_id = ?
            """, (engagement.opportunity_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Validate user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", 
                      (engagement.created_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("""
            INSERT INTO influencer_engagements (
                influencer_id, opportunity_id, engagement_date,
                engagement_type, description, outcome,
                next_steps, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            engagement.influencer_id, engagement.opportunity_id,
            engagement.engagement_date.isoformat(),
            engagement.engagement_type, engagement.description,
            engagement.outcome, engagement.next_steps,
            engagement.created_by
        ))
        
        engagement_id = cursor.lastrowid
        db.commit()
        
        # Get created engagement
        cursor.execute("""
            SELECT 
                e.*,
                i.first_name || ' ' || i.last_name as influencer_name,
                o.opportunity_name,
                u.full_name as created_by_name
            FROM influencer_engagements e
            LEFT JOIN influencers i ON e.influencer_id = i.influencer_id
            LEFT JOIN opportunities o ON e.opportunity_id = o.opportunity_id
            LEFT JOIN users u ON e.created_by = u.user_id
            WHERE e.engagement_id = ?
        """, (engagement_id,))
        created_engagement = dict(cursor.fetchone())
        
        return created_engagement
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.put("/{engagement_id}")
async def update_engagement(
    engagement_id: int = Path(..., ge=1),
    engagement: EngagementUpdate = Body(...)
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if engagement exists
        cursor.execute("""
            SELECT engagement_id 
            FROM influencer_engagements 
            WHERE engagement_id = ?
        """, (engagement_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Build update query
        update_fields = []
        params = []
        
        if engagement.engagement_type is not None:
            update_fields.append("engagement_type = ?")
            params.append(engagement.engagement_type)
        
        if engagement.description is not None:
            update_fields.append("description = ?")
            params.append(engagement.description)
        
        if engagement.outcome is not None:
            update_fields.append("outcome = ?")
            params.append(engagement.outcome)
        
        if engagement.next_steps is not None:
            update_fields.append("next_steps = ?")
            params.append(engagement.next_steps)
        
        if update_fields:
            query = f"""
                UPDATE influencer_engagements 
                SET {', '.join(update_fields)}
                WHERE engagement_id = ?
            """
            params.append(engagement_id)
            
            cursor.execute(query, params)
            db.commit()
        
        # Get updated engagement
        cursor.execute("""
            SELECT 
                e.*,
                i.first_name || ' ' || i.last_name as influencer_name,
                o.opportunity_name,
                u.full_name as created_by_name
            FROM influencer_engagements e
            LEFT JOIN influencers i ON e.influencer_id = i.influencer_id
            LEFT JOIN opportunities o ON e.opportunity_id = o.opportunity_id
            LEFT JOIN users u ON e.created_by = u.user_id
            WHERE e.engagement_id = ?
        """, (engagement_id,))
        updated_engagement = dict(cursor.fetchone())
        
        return updated_engagement
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.delete("/{engagement_id}")
async def delete_engagement(engagement_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if engagement exists
        cursor.execute("""
            SELECT engagement_id 
            FROM influencer_engagements 
            WHERE engagement_id = ?
        """, (engagement_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        cursor.execute("DELETE FROM influencer_engagements WHERE engagement_id = ?", 
                      (engagement_id,))
        db.commit()
        
        return {"message": "Engagement deleted successfully"}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 