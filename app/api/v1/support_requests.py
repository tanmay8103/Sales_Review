from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from sqlite3 import Error
from .database import get_db

router = APIRouter(prefix="/api/support-requests", tags=["Support Requests"])

class SupportRequestBase(BaseModel):
    opportunity_id: int
    request_type: str
    description: str
    priority: str
    status: str
    requested_by: int
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class SupportRequestCreate(SupportRequestBase):
    pass

class SupportRequestUpdate(BaseModel):
    request_type: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    resolution: Optional[str] = None
    resolved_date: Optional[datetime] = None

@router.get("")
async def list_support_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    opportunity_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    request_type: Optional[str] = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                sr.*,
                o.opportunity_name,
                requester.full_name as requested_by_name,
                assignee.full_name as assigned_to_name
            FROM support_requests sr
            LEFT JOIN opportunities o ON sr.opportunity_id = o.opportunity_id
            LEFT JOIN users requester ON sr.requested_by = requester.user_id
            LEFT JOIN users assignee ON sr.assigned_to = assignee.user_id
            WHERE 1=1
        """
        params = []
        
        if opportunity_id:
            query += " AND sr.opportunity_id = ?"
            params.append(opportunity_id)
        
        if status:
            query += " AND sr.status = ?"
            params.append(status)
        
        if priority:
            query += " AND sr.priority = ?"
            params.append(priority)
        
        if assigned_to:
            query += " AND sr.assigned_to = ?"
            params.append(assigned_to)
        
        if request_type:
            query += " AND sr.request_type = ?"
            params.append(request_type)
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                sr.*,\n                o.opportunity_name,\n                requester.full_name as requested_by_name,\n                assignee.full_name as assigned_to_name",
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * limit
        query += " ORDER BY sr.created_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        requests = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": requests
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{request_id}")
async def get_support_request(request_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                sr.*,
                o.opportunity_name,
                o.stage_name as opportunity_stage,
                o.total_amount as opportunity_amount,
                requester.full_name as requested_by_name,
                requester.email as requested_by_email,
                assignee.full_name as assigned_to_name,
                assignee.email as assigned_to_email
            FROM support_requests sr
            LEFT JOIN opportunities o ON sr.opportunity_id = o.opportunity_id
            LEFT JOIN users requester ON sr.requested_by = requester.user_id
            LEFT JOIN users assignee ON sr.assigned_to = assignee.user_id
            WHERE sr.request_id = ?
        """, (request_id,))
        
        request = cursor.fetchone()
        if not request:
            raise HTTPException(status_code=404, detail="Support request not found")
        
        return dict(request)
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("")
async def create_support_request(request: SupportRequestCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate opportunity exists
        cursor.execute("SELECT opportunity_id FROM opportunities WHERE opportunity_id = ?",
                      (request.opportunity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Validate requester exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?",
                      (request.requested_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Requester not found")
        
        # Validate assignee if provided
        if request.assigned_to:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?",
                         (request.assigned_to,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Assignee not found")
        
        cursor.execute("""
            INSERT INTO support_requests (
                opportunity_id, request_type, description,
                priority, status, requested_by,
                assigned_to, due_date, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            request.opportunity_id, request.request_type,
            request.description, request.priority,
            request.status, request.requested_by,
            request.assigned_to,
            request.due_date.isoformat() if request.due_date else None
        ))
        
        request_id = cursor.lastrowid
        db.commit()
        
        # Get created request
        cursor.execute("""
            SELECT 
                sr.*,
                o.opportunity_name,
                requester.full_name as requested_by_name,
                assignee.full_name as assigned_to_name
            FROM support_requests sr
            LEFT JOIN opportunities o ON sr.opportunity_id = o.opportunity_id
            LEFT JOIN users requester ON sr.requested_by = requester.user_id
            LEFT JOIN users assignee ON sr.assigned_to = assignee.user_id
            WHERE sr.request_id = ?
        """, (request_id,))
        created_request = dict(cursor.fetchone())
        
        return created_request
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.put("/{request_id}")
async def update_support_request(
    request_id: int = Path(..., ge=1),
    request: SupportRequestUpdate = Body(...)
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if request exists
        cursor.execute("""
            SELECT request_id 
            FROM support_requests 
            WHERE request_id = ?
        """, (request_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Support request not found")
        
        # Validate assignee if provided
        if request.assigned_to is not None:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?",
                         (request.assigned_to,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Assignee not found")
        
        # Build update query
        update_fields = []
        params = []
        
        if request.request_type is not None:
            update_fields.append("request_type = ?")
            params.append(request.request_type)
        
        if request.description is not None:
            update_fields.append("description = ?")
            params.append(request.description)
        
        if request.priority is not None:
            update_fields.append("priority = ?")
            params.append(request.priority)
        
        if request.status is not None:
            update_fields.append("status = ?")
            params.append(request.status)
            
            # If status is changed to resolved, set resolved_date
            if request.status.lower() in ['resolved', 'completed', 'closed']:
                update_fields.append("resolved_date = datetime('now')")
        
        if request.assigned_to is not None:
            update_fields.append("assigned_to = ?")
            params.append(request.assigned_to)
        
        if request.due_date is not None:
            update_fields.append("due_date = ?")
            params.append(request.due_date.isoformat())
        
        if request.resolution is not None:
            update_fields.append("resolution = ?")
            params.append(request.resolution)
        
        if request.resolved_date is not None:
            update_fields.append("resolved_date = ?")
            params.append(request.resolved_date.isoformat())
        
        if update_fields:
            query = f"""
                UPDATE support_requests 
                SET {', '.join(update_fields)}
                WHERE request_id = ?
            """
            params.append(request_id)
            
            cursor.execute(query, params)
            db.commit()
        
        # Get updated request
        cursor.execute("""
            SELECT 
                sr.*,
                o.opportunity_name,
                requester.full_name as requested_by_name,
                assignee.full_name as assigned_to_name
            FROM support_requests sr
            LEFT JOIN opportunities o ON sr.opportunity_id = o.opportunity_id
            LEFT JOIN users requester ON sr.requested_by = requester.user_id
            LEFT JOIN users assignee ON sr.assigned_to = assignee.user_id
            WHERE sr.request_id = ?
        """, (request_id,))
        updated_request = dict(cursor.fetchone())
        
        return updated_request
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.delete("/{request_id}")
async def delete_support_request(request_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if request exists
        cursor.execute("""
            SELECT request_id 
            FROM support_requests 
            WHERE request_id = ?
        """, (request_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Support request not found")
        
        cursor.execute("DELETE FROM support_requests WHERE request_id = ?",
                      (request_id,))
        db.commit()
        
        return {"message": "Support request deleted successfully"}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 