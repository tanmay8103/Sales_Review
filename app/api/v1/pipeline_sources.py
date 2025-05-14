from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
import sqlite3
from pydantic import BaseModel

router = APIRouter(prefix="/api/pipeline-sources", tags=["Pipeline Sources"])

class PipelineSourceBase(BaseModel):
    source_name: str
    description: Optional[str] = None
    is_active: bool = True

class PipelineSourceCreate(PipelineSourceBase):
    pass

class PipelineSourceUpdate(PipelineSourceBase):
    source_name: Optional[str] = None
    is_active: Optional[bool] = None

def get_db():
    conn = sqlite3.connect('sales_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.get("")
async def list_pipeline_sources(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Base query
        query = "SELECT * FROM pipeline_sources WHERE 1=1"
        params = []
        
        if search:
            query += " AND source_name LIKE ?"
            params.append(f"%{search}%")
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * limit
        query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, params)
        sources = [dict(row) for row in cursor.fetchall()]
        
        return {
            "totalRecords": total_records,
            "totalPages": (total_records + limit - 1) // limit,
            "currentPage": page,
            "data": sources
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{source_id}")
async def get_pipeline_source(source_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT * FROM pipeline_sources WHERE source_id = ?
        """, (source_id,))
        
        source = cursor.fetchone()
        if not source:
            raise HTTPException(status_code=404, detail="Pipeline source not found")
        
        return dict(source)
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("")
async def create_pipeline_source(source: PipelineSourceCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO pipeline_sources (source_name, description, is_active)
            VALUES (?, ?, ?)
        """, (source.source_name, source.description, source.is_active))
        
        source_id = cursor.lastrowid
        db.commit()
        
        # Get created source
        cursor.execute("SELECT * FROM pipeline_sources WHERE source_id = ?", 
                      (source_id,))
        created_source = dict(cursor.fetchone())
        
        return created_source
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.put("/{source_id}")
async def update_pipeline_source(
    source_id: int = Path(..., ge=1),
    source: PipelineSourceUpdate
):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if source exists
        cursor.execute("SELECT source_id FROM pipeline_sources WHERE source_id = ?", 
                      (source_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pipeline source not found")
        
        # Build update query
        update_fields = []
        params = []
        
        if source.source_name is not None:
            update_fields.append("source_name = ?")
            params.append(source.source_name)
        
        if source.description is not None:
            update_fields.append("description = ?")
            params.append(source.description)
        
        if source.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(source.is_active)
        
        if update_fields:
            update_fields.append("last_modified_date = datetime('now')")
            query = f"""
                UPDATE pipeline_sources 
                SET {', '.join(update_fields)}
                WHERE source_id = ?
            """
            params.append(source_id)
            
            cursor.execute(query, params)
            db.commit()
        
        # Get updated source
        cursor.execute("SELECT * FROM pipeline_sources WHERE source_id = ?", 
                      (source_id,))
        updated_source = dict(cursor.fetchone())
        
        return updated_source
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.delete("/{source_id}")
async def delete_pipeline_source(source_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if source exists
        cursor.execute("SELECT source_id FROM pipeline_sources WHERE source_id = ?", 
                      (source_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Pipeline source not found")
        
        # Check if source is being used by any opportunities
        cursor.execute("""
            SELECT COUNT(*) FROM opportunities WHERE source_id = ?
        """, (source_id,))
        if cursor.fetchone()[0] > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete source that is being used by opportunities"
            )
        
        cursor.execute("DELETE FROM pipeline_sources WHERE source_id = ?", 
                      (source_id,))
        db.commit()
        
        return {"message": "Pipeline source deleted successfully"}
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 