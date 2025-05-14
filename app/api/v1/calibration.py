from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from sqlite3 import Error
from .database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/calibration", tags=["Calibration"])

@router.get("")
async def get_calibration(user_id: Optional[int] = Query(None)):
    try:
        db = get_db()
        cursor = db.cursor()

        def get_quarter_metrics(year: int, quarter: str, user_id: Optional[int] = None) -> dict:
            # Get targets
            target_query = """
                SELECT 
                    revenue_target,
                    pipeline_target,
                    deals_target
                FROM quarterly_targets
                WHERE fiscal_year = ? AND fiscal_quarter = ?
            """
            params = [year, quarter]
            
            if user_id:
                target_query += " AND user_id = ?"
                params.append(user_id)
            else:
                target_query += " AND user_id IS NULL"
                
            cursor.execute(target_query, params)
            target = cursor.fetchone()
            
            if not target:
                return None
                
            # Get actual metrics
            metrics_query = """
                SELECT 
                    SUM(total_amount) as actual_revenue,
                    COUNT(*) as deals_count
                FROM opportunities
                WHERE fiscal_year = ? 
                AND fiscal_quarter = ?
                AND status = 'Closed Won'
            """
            params = [year, quarter]
            
            if user_id:
                metrics_query += " AND owner_id = ?"
                params.append(user_id)
                
            cursor.execute(metrics_query, params)
            actuals = cursor.fetchone()
            
            # Get pipeline
            pipeline_query = """
                SELECT 
                    SUM(total_amount) as pipeline_amount,
                    SUM(total_amount * (probability_percentage / 100)) as weighted_pipeline
                FROM opportunities
                WHERE fiscal_year = ? 
                AND fiscal_quarter = ?
                AND status = 'Open'
            """
            params = [year, quarter]
            
            if user_id:
                pipeline_query += " AND owner_id = ?"
                params.append(user_id)
                
            cursor.execute(pipeline_query, params)
            pipeline = cursor.fetchone()
            
            actual_revenue = actuals['actual_revenue'] or 0
            pipeline_amount = pipeline['pipeline_amount'] or 0
            weighted_pipeline = pipeline['weighted_pipeline'] or 0
            
            completion_percentage = (actual_revenue / target['revenue_target'] * 100) if target['revenue_target'] > 0 else 0
            
            return {
                "fiscal_year": year,
                "fiscal_quarter": quarter,
                "revenue_target": target['revenue_target'],
                "pipeline_target": target['pipeline_target'],
                "deals_target": target['deals_target'],
                "actual_revenue": actual_revenue,
                "pipeline_amount": pipeline_amount,
                "weighted_pipeline": weighted_pipeline,
                "completion_percentage": completion_percentage
            }

        # Get current quarter
        now = datetime.now()
        current_year = now.year
        month = now.month
        current_quarter = f"Q{(month - 1) // 3 + 1}"

        current_metrics = get_quarter_metrics(current_year, current_quarter, user_id)
        if not current_metrics:
            raise HTTPException(status_code=404, detail="Current quarter targets not found")

        return current_metrics

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 