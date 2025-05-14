from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from sqlite3 import Error
from .database import get_db
from pydantic import BaseModel

class AccountUpdate(BaseModel):
    account_name: str

class AccountCreate(BaseModel):
    account_id: Optional[int] = None
    account_name: str

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

@router.get("")
async def list_accounts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    try:
        db = get_db()
        cursor = db.cursor()

        # Get all accounts with their data
        cursor.execute("""
            SELECT 
                a.account_id,
                a.account_name,
                a.created_at,
                COUNT(DISTINCT o.opportunity_id) as opportunity_count,
                SUM(CASE WHEN o.is_closed = 0 THEN o.total_amount ELSE 0 END) as open_opportunity_value,
                SUM(CASE WHEN o.is_closed = 1 AND o.is_won = 1 THEN o.total_amount ELSE 0 END) as won_opportunity_value
            FROM accounts a
            LEFT JOIN opportunities o ON a.account_id = o.account_id
            GROUP BY a.account_id, a.account_name, a.created_at
        """)
        
        accounts = [dict(row) for row in cursor.fetchall()]
        
        # Calculate pagination
        total_records = len(accounts)
        total_pages = (total_records + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return {
            "totalRecords": total_records,
            "totalPages": total_pages,
            "currentPage": page,
            "data": accounts[start_idx:end_idx]
        }

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.get("/{account_id}")
async def get_account(account_id: int = Path(..., ge=1)):
    try:
        db = get_db()
        cursor = db.cursor()

        # Get account details
        cursor.execute("""
            SELECT * FROM accounts 
            WHERE account_id = ?
        """, (account_id,))
        account = cursor.fetchone()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        account_dict = dict(account)

        # Get opportunities for this account with all fields
        cursor.execute("""
            SELECT 
                o.opportunity_id,
                o.opportunity_name,
                o.total_amount,
                o.currency,
                o.stage_name,
                o.close_date,
                o.probability_percentage,
                o.type,
                o.fiscal_period,
                o.opportunity_owner,
                o.next_step,
                o.lead_source,
                o.annual_contract_value,
                o.contract_duration_months,
                o.fiscal_year,
                o.fiscal_quarter,
                o.is_closed,
                o.is_won,
                s.stage_name as current_stage_name,
                ps.source_name
            FROM opportunities o
            LEFT JOIN stages s ON o.stage_id = s.stage_id
            LEFT JOIN pipeline_sources ps ON o.source_id = ps.source_id
            WHERE o.account_id = ?
            ORDER BY o.created_date DESC
        """, (account_id,))
        
        opportunities = [dict(row) for row in cursor.fetchall()]
        account_dict['opportunities'] = opportunities

        # Format dates
        if 'created_at' in account_dict:
            account_dict['created_at'] = account_dict['created_at'].split()[0]

        return account_dict

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.put("/{account_id}")
async def update_account(
    account_id: int = Path(..., ge=1),
    account: AccountUpdate = None
):
    try:
        db = get_db()
        cursor = db.cursor()

        # Check if account exists
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = ?", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")

        # Update account
        cursor.execute("""
            UPDATE accounts 
            SET account_name = ?
            WHERE account_id = ?
        """, (account.account_name, account_id))

        db.commit()
        return {"message": "Account updated successfully"}

    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@router.post("")
async def create_account(account: AccountCreate):
    try:
        db = get_db()
        cursor = db.cursor()

        # Check if account with same name already exists
        cursor.execute("SELECT account_id FROM accounts WHERE account_name = ?", (account.account_name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Account with this name already exists")

        # If account_id is provided, check if it's available
        if account.account_id:
            cursor.execute("SELECT account_id FROM accounts WHERE account_id = ?", (account.account_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Account with ID {account.account_id} already exists")
            
            # Insert with specific ID
            cursor.execute("""
                INSERT INTO accounts (account_id, account_name)
                VALUES (?, ?)
            """, (account.account_id, account.account_name))
        else:
            # Let SQLite auto-generate the ID
            cursor.execute("""
                INSERT INTO accounts (account_name)
                VALUES (?)
            """, (account.account_name,))

        db.commit()
        return {"message": "Account created successfully", "account_id": cursor.lastrowid or account.account_id}

    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close() 