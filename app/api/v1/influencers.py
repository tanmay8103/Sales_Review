from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List
from datetime import datetime
import sqlite3
from pydantic import BaseModel, EmailStr
from .database import get_db

router = APIRouter(prefix="/api/influencers", tags=["Influencers"])

class InfluencerBase(BaseModel):
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    account_id: int
    role: str
    influence_level: str
    notes: Optional[str] = None

class InfluencerCreate(InfluencerBase):
    pass

class InfluencerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    influence_level: Optional[str] = None
    notes: Optional[str] = None

class EngagementCreate(BaseModel):
    influencer_id: int
    opportunity_id: int
    engagement_date: datetime
    engagement_type: str
    description: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    created_by: int

@router.get("")
async def get_influencers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    account_id: Optional[int] = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                i.*,
                a.account_name,
                COUNT(DISTINCT ie.engagement_id) as total_engagements,
                COUNT(DISTINCT ie.opportunity_id) as total_opportunities
            FROM influencers i
            LEFT JOIN accounts a ON i.account_id = a.account_id
            LEFT JOIN influencer_engagements ie ON i.influencer_id = ie.influencer_id
            WHERE 1=1
        """
        params = []
        
        if account_id:
            query += " AND i.account_id = ?"
            params.append(account_id)
            
        query += " GROUP BY i.influencer_id"
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                i.*,\n                a.account_name,\n                COUNT(DISTINCT ie.engagement_id) as total_engagements,\n                COUNT(DISTINCT ie.opportunity_id) as total_opportunities",
            "SELECT COUNT(DISTINCT i.influencer_id)"
        )
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * limit
        query += " ORDER BY i.last_name, i.first_name LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        influencers = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": influencers
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{influencer_id}")
async def get_influencer(influencer_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get influencer details
        cursor.execute("""
            SELECT 
                i.*,
                a.account_name
            FROM influencers i
            LEFT JOIN accounts a ON i.account_id = a.account_id
            WHERE i.influencer_id = ?
        """, (influencer_id,))
        
        influencer = cursor.fetchone()
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")
            
        influencer_dict = dict(influencer)
        
        # Get engagements for this influencer
        cursor.execute("""
            SELECT 
                ie.*,
                o.opportunity_name,
                u.full_name as created_by_name
            FROM influencer_engagements ie
            LEFT JOIN opportunities o ON ie.opportunity_id = o.opportunity_id
            LEFT JOIN users u ON ie.created_by = u.user_id
            WHERE ie.influencer_id = ?
            ORDER BY ie.engagement_date DESC
        """, (influencer_id,))
        
        engagements = [dict(row) for row in cursor.fetchall()]
        influencer_dict['engagements'] = engagements
        
        return influencer_dict
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("")
async def create_influencer(influencer: InfluencerCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate account exists if provided
        if influencer.account_id:
            cursor.execute("SELECT account_id FROM accounts WHERE account_id = ?", 
                         (influencer.account_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Account not found")
        
        cursor.execute("""
            INSERT INTO influencers (
                first_name, last_name, title, email, phone,
                account_id, role, influence_level, notes,
                created_date, last_modified_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            influencer.first_name, influencer.last_name,
            influencer.title, influencer.email, influencer.phone,
            influencer.account_id, influencer.role,
            influencer.influence_level, influencer.notes
        ))
        
        influencer_id = cursor.lastrowid
        db.commit()
        
        return {"message": "Influencer created successfully", "influencer_id": influencer_id}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.patch("/{influencer_id}")
async def update_influencer(
    influencer_id: int = Path(..., ge=1),
    influencer: InfluencerUpdate = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if influencer exists
        cursor.execute("SELECT influencer_id FROM influencers WHERE influencer_id = ?", 
                      (influencer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Validate account exists if provided
        if influencer.account_id:
            cursor.execute("SELECT account_id FROM accounts WHERE account_id = ?", 
                         (influencer.account_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Account not found")
        
        # Build update query
        update_fields = []
        params = []
        
        if influencer.first_name is not None:
            update_fields.append("first_name = ?")
            params.append(influencer.first_name)
        if influencer.last_name is not None:
            update_fields.append("last_name = ?")
            params.append(influencer.last_name)
        if influencer.title is not None:
            update_fields.append("title = ?")
            params.append(influencer.title)
        if influencer.email is not None:
            update_fields.append("email = ?")
            params.append(influencer.email)
        if influencer.phone is not None:
            update_fields.append("phone = ?")
            params.append(influencer.phone)
        if influencer.account_id is not None:
            update_fields.append("account_id = ?")
            params.append(influencer.account_id)
        if influencer.role is not None:
            update_fields.append("role = ?")
            params.append(influencer.role)
        if influencer.influence_level is not None:
            update_fields.append("influence_level = ?")
            params.append(influencer.influence_level)
        if influencer.notes is not None:
            update_fields.append("notes = ?")
            params.append(influencer.notes)
            
        if not update_fields:
            return {"message": "No fields to update"}
            
        update_fields.append("last_modified_date = datetime('now')")
        params.append(influencer_id)
        
        query = f"""
            UPDATE influencers 
            SET {', '.join(update_fields)}
            WHERE influencer_id = ?
        """
        cursor.execute(query, params)
        
        db.commit()
        return {"message": "Influencer updated successfully"}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.delete("/{influencer_id}")
async def delete_influencer(influencer_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if influencer exists
        cursor.execute("SELECT influencer_id FROM influencers WHERE influencer_id = ?", 
                      (influencer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Check if influencer has any engagements
        cursor.execute("""
            SELECT COUNT(*) FROM influencer_engagements 
            WHERE influencer_id = ?
        """, (influencer_id,))
        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete influencer with existing engagements"
            )
        
        cursor.execute("DELETE FROM influencers WHERE influencer_id = ?", 
                      (influencer_id,))
        db.commit()
        
        return {"message": "Influencer deleted successfully"}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("/engagements")
async def create_engagement(engagement: EngagementCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate influencer exists
        cursor.execute("SELECT influencer_id FROM influencers WHERE influencer_id = ?", 
                      (engagement.influencer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Validate opportunity exists
        cursor.execute("SELECT opportunity_id FROM opportunities WHERE opportunity_id = ?", 
                      (engagement.opportunity_id,))
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
                engagement_type, description, outcome, next_steps,
                created_by, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            engagement.influencer_id, engagement.opportunity_id,
            engagement.engagement_date, engagement.engagement_type,
            engagement.description, engagement.outcome,
            engagement.next_steps, engagement.created_by
        ))
        
        engagement_id = cursor.lastrowid
        db.commit()
        
        return {"message": "Engagement created successfully", "engagement_id": engagement_id}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/opportunities/{opportunity_id}")
async def get_opportunity_influencers(opportunity_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate opportunity exists
        cursor.execute("SELECT opportunity_id FROM opportunities WHERE opportunity_id = ?", 
                      (opportunity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Get influencers and their engagements for this opportunity
        cursor.execute("""
            SELECT 
                i.*,
                a.account_name,
                ie.engagement_id,
                ie.engagement_date,
                ie.engagement_type,
                ie.description as engagement_description,
                ie.outcome,
                ie.next_steps,
                u.full_name as created_by_name
            FROM influencer_engagements ie
            JOIN influencers i ON ie.influencer_id = i.influencer_id
            LEFT JOIN accounts a ON i.account_id = a.account_id
            LEFT JOIN users u ON ie.created_by = u.user_id
            WHERE ie.opportunity_id = ?
            ORDER BY ie.engagement_date DESC
        """, (opportunity_id,))
        
        influencers = [dict(row) for row in cursor.fetchall()]
        return influencers
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/opportunities/{opportunity_id}/influencers")
async def get_opportunity_influencers_simple(opportunity_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate opportunity exists
        cursor.execute("SELECT opportunity_id FROM opportunities WHERE opportunity_id = ?", 
                      (opportunity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Get just the influencers for this opportunity
        cursor.execute("""
            SELECT DISTINCT
                i.influencer_id,
                i.first_name,
                i.last_name,
                i.title,
                i.email,
                i.phone,
                i.account_id,
                a.account_name,
                i.role,
                i.influence_level
            FROM influencer_engagements ie
            JOIN influencers i ON ie.influencer_id = i.influencer_id
            LEFT JOIN accounts a ON i.account_id = a.account_id
            WHERE ie.opportunity_id = ?
            ORDER BY i.last_name, i.first_name
        """, (opportunity_id,))
        
        influencers = [dict(row) for row in cursor.fetchall()]
        return influencers
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 