from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from sqlite3 import Error
from .database import get_db

router = APIRouter(prefix="/api/sales-review", tags=["Sales Review"])

@router.get("")
async def get_sales_review(
    user_id: Optional[int] = Query(None),
    fiscal_year: Optional[int] = Query(None),
    fiscal_quarter: Optional[str] = Query(None)
):
    try:
        db = get_db()
        cursor = db.cursor()

        # Current Opportunities
        opportunity_query = """
            SELECT 
                o.*,
                a.account_name,
                u.full_name as owner_name,
                ps.source_name,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.account_id
            LEFT JOIN users u ON o.owner_id = u.user_id
            LEFT JOIN pipeline_sources ps ON o.source_id = ps.source_id
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            WHERE o.is_closed = 0
        """
        
        if user_id:
            opportunity_query += " AND o.owner_id = ?"
            cursor.execute(opportunity_query, (user_id,))
        else:
            cursor.execute(opportunity_query)
            
        current_opportunities = [dict(row) for row in cursor.fetchall()]

        # Open Support Requests
        cursor.execute("""
            SELECT 
                sr.*,
                o.opportunity_name,
                a.account_name,
                requester.full_name as requested_by_name,
                assignee.full_name as assigned_to_name
            FROM support_requests sr
            LEFT JOIN opportunities o ON sr.opportunity_id = o.opportunity_id
            LEFT JOIN accounts a ON o.account_id = a.account_id
            LEFT JOIN users requester ON sr.requested_by = requester.user_id
            LEFT JOIN users assignee ON sr.assigned_to = assignee.user_id
            WHERE sr.status NOT IN ('Resolved', 'Completed', 'Closed')
            ORDER BY sr.created_date DESC
        """)
        open_requests = [dict(row) for row in cursor.fetchall()]

        # Deals Closed This Week
        cursor.execute("""
            SELECT 
                dc.*,
                o.opportunity_name,
                a.account_name,
                u.full_name as owner_name,
                ps.source_name
            FROM deals_closed dc
            LEFT JOIN opportunities o ON dc.opportunity_id = o.opportunity_id
            LEFT JOIN accounts a ON dc.account_id = a.account_id
            LEFT JOIN users u ON dc.owner_id = u.user_id
            LEFT JOIN pipeline_sources ps ON dc.source_id = ps.source_id
            WHERE dc.close_date >= date('now', '-7 days')
            ORDER BY dc.close_date DESC
        """)
        closed_deals = [dict(row) for row in cursor.fetchall()]

        return {
            "current_opportunities": current_opportunities,
            "open_support_requests": open_requests,
            "deals_closed_this_week": closed_deals
        }

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 