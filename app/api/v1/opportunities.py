from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from datetime import date
from sqlite3 import Error
from .database import get_db
from pydantic import BaseModel
from typing import Optional as OptionalType

class ProjectPlanUpdate(BaseModel):
    activity: OptionalType[str] = None
    deliverables: OptionalType[str] = None
    priority: OptionalType[str] = None
    due_date: OptionalType[date] = None
    status: OptionalType[str] = None

class OpportunityUpdate(BaseModel):
    opportunity_name: OptionalType[str] = None
    next_step: OptionalType[str] = None
    total_amount: OptionalType[float] = None
    currency: OptionalType[str] = None
    stage_name: OptionalType[str] = None
    probability_percentage: OptionalType[int] = None
    type: OptionalType[str] = None
    fiscal_period: OptionalType[str] = None
    lead_source: OptionalType[str] = None
    blockers: OptionalType[str] = None
    support_needed: OptionalType[str] = None
    project_plan: OptionalType[ProjectPlanUpdate] = None
    changed_by: OptionalType[int] = None  # User ID who made the change

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])

@router.get("")
async def get_opportunities(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    accountId: Optional[int] = None,
    ownerId: Optional[int] = None,
    stageId: Optional[int] = None,
    fiscalPeriod: Optional[str] = None,
    closeDateStart: Optional[date] = None,
    closeDateEnd: Optional[date] = None,
    minAmount: Optional[float] = None,
    maxAmount: Optional[float] = None,
    type: Optional[str] = None,
    leadSource: Optional[str] = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                o.*,
                a.account_name,
                u.full_name as owner_name,
                s.stage_name as current_stage_name,
                ps.source_name,
                o.blockers,
                o.support_needed,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status,
                GROUP_CONCAT(DISTINCT i.influencer_id || ':' || i.first_name || ' ' || i.last_name || ':' || i.title || ':' || i.role || ':' || i.influence_level) as influencers
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.account_id
            LEFT JOIN users u ON o.owner_id = u.user_id
            LEFT JOIN stages s ON o.stage_id = s.stage_id
            LEFT JOIN pipeline_sources ps ON o.source_id = ps.source_id
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            LEFT JOIN influencer_engagements ie ON o.opportunity_id = ie.opportunity_id
            LEFT JOIN influencers i ON ie.influencer_id = i.influencer_id
            WHERE 1=1
        """
        params = []

        if accountId:
            query += " AND o.account_id = ?"
            params.append(accountId)
        
        if ownerId:
            query += " AND o.owner_id = ?"
            params.append(ownerId)
            
        if stageId:
            query += " AND o.stage_id = ?"
            params.append(stageId)
            
        if fiscalPeriod:
            query += " AND o.fiscal_period = ?"
            params.append(fiscalPeriod)
            
        if closeDateStart:
            query += " AND o.close_date >= ?"
            params.append(closeDateStart)
            
        if closeDateEnd:
            query += " AND o.close_date <= ?"
            params.append(closeDateEnd)
            
        if minAmount:
            query += " AND o.total_amount >= ?"
            params.append(minAmount)
            
        if maxAmount:
            query += " AND o.total_amount <= ?"
            params.append(maxAmount)
            
        if type:
            query += " AND o.type = ?"
            params.append(type)
            
        if leadSource:
            query += " AND o.lead_source = ?"
            params.append(leadSource)

        query += " GROUP BY o.opportunity_id"

        # Get total count
        count_query = query.replace(
            "SELECT \n                o.*,\n                a.account_name,\n                u.full_name as owner_name,\n                s.stage_name as current_stage_name,\n                ps.source_name,\n                o.blockers,\n                o.support_needed,\n                pp.activity as project_activity,\n                pp.deliverables as project_deliverables,\n                pp.priority as project_priority,\n                pp.due_date as project_due_date,\n                pp.status as project_status,\n                GROUP_CONCAT(DISTINCT i.influencer_id || ':' || i.first_name || ' ' || i.last_name || ':' || i.title || ':' || i.role || ':' || i.influence_level) as influencers",
            "SELECT COUNT(DISTINCT o.opportunity_id)"
        )
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]

        # Add pagination
        offset = (page - 1) * limit
        query += " ORDER BY o.created_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        opportunities = [dict(row) for row in cursor.fetchall()]

        # Process influencers string into a list of dictionaries
        for opportunity in opportunities:
            if opportunity.get('influencers'):
                influencer_list = []
                for influencer_str in opportunity['influencers'].split(','):
                    if influencer_str:
                        id, name, title, role, influence_level = influencer_str.split(':')
                        influencer_list.append({
                            'influencer_id': int(id),
                            'name': name,
                            'title': title,
                            'role': role,
                            'influence_level': influence_level
                        })
                opportunity['influencers'] = influencer_list
            else:
                opportunity['influencers'] = []

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

@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 
                o.*,
                a.account_name,
                u.full_name as owner_name,
                s.stage_name as current_stage_name,
                ps.source_name,
                o.blockers,
                o.support_needed,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status,
                GROUP_CONCAT(DISTINCT i.influencer_id || ':' || i.first_name || ' ' || i.last_name || ':' || i.title || ':' || i.role || ':' || i.influence_level) as influencers
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.account_id
            LEFT JOIN users u ON o.owner_id = u.user_id
            LEFT JOIN stages s ON o.stage_id = s.stage_id
            LEFT JOIN pipeline_sources ps ON o.source_id = ps.source_id
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            LEFT JOIN influencer_engagements ie ON o.opportunity_id = ie.opportunity_id
            LEFT JOIN influencers i ON ie.influencer_id = i.influencer_id
            WHERE o.opportunity_id = ?
            GROUP BY o.opportunity_id
        """, (opportunity_id,))
        
        opportunity = cursor.fetchone()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
            
        opportunity_dict = dict(opportunity)
        
        # Process influencers string into a list of dictionaries
        if opportunity_dict.get('influencers'):
            influencer_list = []
            for influencer_str in opportunity_dict['influencers'].split(','):
                if influencer_str:
                    id, name, title, role, influence_level = influencer_str.split(':')
                    influencer_list.append({
                        'influencer_id': int(id),
                        'name': name,
                        'title': title,
                        'role': role,
                        'influence_level': influence_level
                    })
            opportunity_dict['influencers'] = influencer_list
        else:
            opportunity_dict['influencers'] = []
            
        return opportunity_dict

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{opportunity_id}/history")
async def get_opportunity_history(
    opportunity_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate opportunity exists
        cursor.execute("SELECT opportunity_id FROM opportunities WHERE opportunity_id = ?", (opportunity_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Get history with user information
        query = """
            SELECT 
                h.*,
                u.full_name as changed_by_name
            FROM opportunity_history h
            LEFT JOIN users u ON h.changed_by = u.user_id
            WHERE h.opportunity_id = ?
            ORDER BY h.changed_at DESC
        """
        
        # Get total count
        count_query = query.replace(
            "SELECT \n                h.*,\n                u.full_name as changed_by_name",
            "SELECT COUNT(*)"
        )
        cursor.execute(count_query, (opportunity_id,))
        total_records = cursor.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * limit
        query += " LIMIT ? OFFSET ?"
        
        cursor.execute(query, (opportunity_id, limit, offset))
        history = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": history
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.patch("/{opportunity_id}")
async def update_opportunity(
    opportunity_id: int = Path(..., ge=1),
    opportunity: OpportunityUpdate = None
):
    try:
        db = get_db()
        cursor = db.cursor()

        # Check if opportunity exists and get current values
        cursor.execute("""
            SELECT 
                o.*,
                pp.activity as project_activity,
                pp.deliverables as project_deliverables,
                pp.priority as project_priority,
                pp.due_date as project_due_date,
                pp.status as project_status
            FROM opportunities o
            LEFT JOIN opportunity_project_plan pp ON o.opportunity_id = pp.opportunity_id
            WHERE o.opportunity_id = ?
        """, (opportunity_id,))
        
        current_opportunity = cursor.fetchone()
        if not current_opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
            
        current_values = dict(current_opportunity)

        # Validate user exists if provided
        if opportunity.changed_by:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (opportunity.changed_by,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        history_entries = []
        
        # Only include fields that are not None
        if opportunity.opportunity_name is not None:
            update_fields.append("opportunity_name = ?")
            params.append(opportunity.opportunity_name)
            history_entries.append(("opportunity_name", current_values.get('opportunity_name'), opportunity.opportunity_name))
            
        if opportunity.next_step is not None:
            update_fields.append("next_step = ?")
            params.append(opportunity.next_step)
            history_entries.append(("next_step", current_values.get('next_step'), opportunity.next_step))
            
        if opportunity.total_amount is not None:
            update_fields.append("total_amount = ?")
            params.append(opportunity.total_amount)
            history_entries.append(("total_amount", current_values.get('total_amount'), opportunity.total_amount))
            
        if opportunity.currency is not None:
            update_fields.append("currency = ?")
            params.append(opportunity.currency)
            history_entries.append(("currency", current_values.get('currency'), opportunity.currency))
            
        if opportunity.stage_name is not None:
            update_fields.append("stage_name = ?")
            params.append(opportunity.stage_name)
            history_entries.append(("stage_name", current_values.get('stage_name'), opportunity.stage_name))
            
        if opportunity.probability_percentage is not None:
            update_fields.append("probability_percentage = ?")
            params.append(opportunity.probability_percentage)
            history_entries.append(("probability_percentage", current_values.get('probability_percentage'), opportunity.probability_percentage))
            
        if opportunity.type is not None:
            update_fields.append("type = ?")
            params.append(opportunity.type)
            history_entries.append(("type", current_values.get('type'), opportunity.type))
            
        if opportunity.fiscal_period is not None:
            update_fields.append("fiscal_period = ?")
            params.append(opportunity.fiscal_period)
            history_entries.append(("fiscal_period", current_values.get('fiscal_period'), opportunity.fiscal_period))
            
        if opportunity.lead_source is not None:
            update_fields.append("lead_source = ?")
            params.append(opportunity.lead_source)
            history_entries.append(("lead_source", current_values.get('lead_source'), opportunity.lead_source))
            
        if opportunity.blockers is not None:
            update_fields.append("blockers = ?")
            params.append(opportunity.blockers)
            history_entries.append(("blockers", current_values.get('blockers'), opportunity.blockers))
            
        if opportunity.support_needed is not None:
            update_fields.append("support_needed = ?")
            params.append(opportunity.support_needed)
            history_entries.append(("support_needed", current_values.get('support_needed'), opportunity.support_needed))

        if not update_fields:
            return {"message": "No fields to update"}

        # Add opportunity_id to params
        params.append(opportunity_id)

        # Execute update
        query = f"""
            UPDATE opportunities 
            SET {', '.join(update_fields)}
            WHERE opportunity_id = ?
        """
        cursor.execute(query, params)

        # Update project plan if provided
        if opportunity.project_plan is not None:
            project_plan = opportunity.project_plan
            project_plan_fields = []
            project_plan_params = []

            if project_plan.activity is not None:
                project_plan_fields.append("activity = ?")
                project_plan_params.append(project_plan.activity)
                history_entries.append(("project_activity", current_values.get('project_activity'), project_plan.activity))
                
            if project_plan.deliverables is not None:
                project_plan_fields.append("deliverables = ?")
                project_plan_params.append(project_plan.deliverables)
                history_entries.append(("project_deliverables", current_values.get('project_deliverables'), project_plan.deliverables))
                
            if project_plan.priority is not None:
                project_plan_fields.append("priority = ?")
                project_plan_params.append(project_plan.priority)
                history_entries.append(("project_priority", current_values.get('project_priority'), project_plan.priority))
                
            if project_plan.due_date is not None:
                project_plan_fields.append("due_date = ?")
                project_plan_params.append(project_plan.due_date)
                history_entries.append(("project_due_date", current_values.get('project_due_date'), project_plan.due_date))
                
            if project_plan.status is not None:
                project_plan_fields.append("status = ?")
                project_plan_params.append(project_plan.status)
                history_entries.append(("project_status", current_values.get('project_status'), project_plan.status))

            if project_plan_fields:
                project_plan_params.append(opportunity_id)
                project_plan_query = f"""
                    UPDATE opportunity_project_plan 
                    SET {', '.join(project_plan_fields)}
                    WHERE opportunity_id = ?
                """
                cursor.execute(project_plan_query, project_plan_params)

        # Record history entries
        if history_entries and opportunity.changed_by:
            history_query = """
                INSERT INTO opportunity_history 
                (opportunity_id, field_name, old_value, new_value, changed_by)
                VALUES (?, ?, ?, ?, ?)
            """
            for field_name, old_value, new_value in history_entries:
                cursor.execute(history_query, (
                    opportunity_id,
                    field_name,
                    str(old_value) if old_value is not None else None,
                    str(new_value) if new_value is not None else None,
                    opportunity.changed_by
                ))

        db.commit()
        return {"message": "Opportunity updated successfully"}

    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 