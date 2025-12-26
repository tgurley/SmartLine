"""
SmartLine Bankroll Manager API Endpoints
==========================================
Complete REST API for bankroll management, bet tracking, and analytics.

Endpoints:
1. POST   /bankroll/accounts - Create sportsbook account
2. GET    /bankroll/accounts - List all accounts
3. PUT    /bankroll/accounts/{account_id} - Update account balance
4. DELETE /bankroll/accounts/{account_id} - Delete account

5. POST   /bankroll/bets - Log a new bet
6. GET    /bankroll/bets - List bets with filters
7. GET    /bankroll/bets/{bet_id} - Get bet details
8. PUT    /bankroll/bets/{bet_id} - Update bet
9. DELETE /bankroll/bets/{bet_id} - Delete bet
10. POST  /bankroll/bets/{bet_id}/settle - Settle a bet

11. GET   /bankroll/analytics/overview - Dashboard overview stats
12. GET   /bankroll/analytics/chart-data - Bankroll chart data
13. GET   /bankroll/analytics/by-bookmaker - Performance by sportsbook
14. GET   /bankroll/analytics/by-market - Performance by market

15. GET   /bankroll/transactions - Transaction history
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize router
router = APIRouter(prefix="/bankroll", tags=["Bankroll Manager"])

# =========================================================
# RESPONSE MODELS
# =========================================================

class BankrollAccountCreate(BaseModel):
    bookmaker_name: str = Field(..., min_length=1, max_length=100)
    starting_balance: Decimal = Field(..., gt=0)

class BankrollAccountUpdate(BaseModel):
    current_balance: Decimal

class BankrollAccount(BaseModel):
    account_id: int
    user_id: int
    bookmaker_name: str
    current_balance: Decimal
    starting_balance: Decimal
    created_at: datetime
    updated_at: datetime

class BetCreate(BaseModel):
    account_id: Optional[int] = None
    bet_type: Literal["player_prop", "game_line", "parlay"]
    sport: str = "NFL"
    game_id: Optional[int] = None
    player_id: Optional[int] = None
    market_key: Optional[str] = None
    bet_side: Optional[Literal["over", "under", "home", "away"]] = None
    line_value: Optional[Decimal] = None
    odds_american: int = Field(..., description="American odds (e.g., -110, +150)")
    stake_amount: Decimal = Field(..., gt=0)
    placed_at: Optional[datetime] = None
    notes: Optional[str] = None

class BetUpdate(BaseModel):
    account_id: Optional[int] = None
    market_key: Optional[str] = None
    bet_side: Optional[str] = None
    line_value: Optional[Decimal] = None
    odds_american: Optional[int] = None
    stake_amount: Optional[Decimal] = None
    notes: Optional[str] = None

class BetSettle(BaseModel):
    status: Literal["won", "lost", "push", "cancelled"]

class Bet(BaseModel):
    bet_id: int
    user_id: int
    account_id: Optional[int]
    bookmaker_name: Optional[str]
    bet_type: str
    sport: str
    player_id: Optional[int]
    player_name: Optional[str]
    player_position: Optional[str]
    player_image_url: Optional[str]
    game_id: Optional[int]
    market_key: Optional[str]
    bet_side: Optional[str]
    line_value: Optional[Decimal]
    odds_american: int
    stake_amount: Decimal
    potential_payout: Optional[Decimal]
    actual_payout: Optional[Decimal]
    profit_loss: Optional[Decimal]
    status: str
    placed_at: datetime
    settled_at: Optional[datetime]
    notes: Optional[str]

class BankrollOverview(BaseModel):
    total_bankroll: Decimal
    available_balance: Decimal
    locked_in_bets: Decimal
    total_profit_loss: Decimal
    roi: Decimal
    win_rate: Decimal
    total_bets: int
    pending_bets: int
    won_bets: int
    lost_bets: int
    push_bets: int
    avg_bet_size: Decimal
    current_streak: dict

class ChartDataPoint(BaseModel):
    date: str
    balance: Decimal
    profit_loss: Decimal

class BookmakerPerformance(BaseModel):
    bookmaker_name: str
    total_bets: int
    won_bets: int
    lost_bets: int
    total_profit_loss: Decimal
    win_rate: Decimal

class MarketPerformance(BaseModel):
    market_key: str
    total_bets: int
    won_bets: int
    lost_bets: int
    total_profit_loss: Decimal
    win_rate: Decimal
    avg_stake: Decimal

class Transaction(BaseModel):
    transaction_id: int
    account_id: int
    user_id: int
    bet_id: Optional[int]
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    description: Optional[str]
    created_at: datetime

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    """Database connection dependency."""
    import os
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", 5432),
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def calculate_payout(odds_american: int, stake: Decimal) -> Decimal:
    """Calculate potential payout from American odds."""
    if odds_american > 0:
        # Positive odds: profit = stake * (odds / 100)
        profit = stake * (Decimal(odds_american) / 100)
    else:
        # Negative odds: profit = stake / (abs(odds) / 100)
        profit = stake / (Decimal(abs(odds_american)) / 100)
    
    return stake + profit

def get_current_streak(cursor, user_id: int):
    """Calculate current betting streak."""
    cursor.execute("""
        SELECT status, placed_at
        FROM bets
        WHERE user_id = %s AND status IN ('won', 'lost')
        ORDER BY placed_at DESC
        LIMIT 20
    """, [user_id])
    
    results = cursor.fetchall()
    
    if not results:
        return {"type": "none", "length": 0}
    
    current_status = results[0]['status']
    streak_length = 0
    
    for bet in results:
        if bet['status'] == current_status:
            streak_length += 1
        else:
            break
    
    return {"type": current_status, "length": streak_length}

# =========================================================
# ACCOUNTS ENDPOINTS
# =========================================================

@router.post("/accounts", response_model=BankrollAccount)
async def create_account(
    account: BankrollAccountCreate,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Create a new sportsbook account.
    
    **Use Case:** Add a new betting account to track
    **Returns:** Created account details
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO bankroll_accounts (user_id, bookmaker_name, starting_balance, current_balance)
            VALUES (%s, %s, %s, %s)
            RETURNING account_id, user_id, bookmaker_name, current_balance, starting_balance, created_at, updated_at
        """, [user_id, account.bookmaker_name, account.starting_balance, account.starting_balance])
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return result
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

@router.get("/accounts", response_model=List[BankrollAccount])
async def get_accounts(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get all sportsbook accounts for a user.
    
    **Use Case:** Display all betting accounts
    **Returns:** List of accounts with balances
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT account_id, user_id, bookmaker_name, current_balance, starting_balance, created_at, updated_at
        FROM bankroll_accounts
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, [user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

@router.put("/accounts/{account_id}", response_model=BankrollAccount)
async def update_account(
    account_id: int,
    account_update: BankrollAccountUpdate,
    conn = Depends(get_db)
):
    """
    Update account balance (manual adjustment).
    
    **Use Case:** Correct account balance or add deposit/withdrawal
    **Returns:** Updated account details
    """
    cursor = conn.cursor()
    
    try:
        # Update account
        cursor.execute("""
            UPDATE bankroll_accounts
            SET current_balance = %s
            WHERE account_id = %s
            RETURNING account_id, user_id, bookmaker_name, current_balance, starting_balance, created_at, updated_at
        """, [account_update.current_balance, account_id])
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Log transaction
        cursor.execute("""
            INSERT INTO bankroll_transactions (account_id, user_id, transaction_type, amount, balance_after, description)
            VALUES (%s, %s, 'adjustment', %s, %s, 'Manual balance adjustment')
        """, [account_id, result['user_id'], account_update.current_balance, account_update.current_balance])
        
        conn.commit()
        cursor.close()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to update account: {str(e)}")

@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int,
    conn = Depends(get_db)
):
    """
    Delete a sportsbook account.
    
    **Use Case:** Remove an account no longer in use
    **Returns:** Success message
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM bankroll_accounts WHERE account_id = %s RETURNING account_id", [account_id])
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Account not found")
        
        conn.commit()
        cursor.close()
        
        return {"message": "Account deleted successfully", "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

# =========================================================
# BETS ENDPOINTS
# =========================================================

@router.post("/bets", response_model=Bet)
async def create_bet(
    bet: BetCreate,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Log a new bet.
    
    **Use Case:** Record a bet placed at a sportsbook
    **Returns:** Created bet details
    """
    cursor = conn.cursor()
    
    try:
        # Calculate potential payout
        potential_payout = calculate_payout(bet.odds_american, bet.stake_amount)
        placed_at = bet.placed_at or datetime.now()
        
        # Insert bet
        cursor.execute("""
            INSERT INTO bets (
                user_id, account_id, bet_type, sport, game_id, player_id,
                market_key, bet_side, line_value, odds_american, stake_amount,
                potential_payout, placed_at, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING bet_id
        """, [
            user_id, bet.account_id, bet.bet_type, bet.sport, bet.game_id, bet.player_id,
            bet.market_key, bet.bet_side, bet.line_value, bet.odds_american, bet.stake_amount,
            potential_payout, placed_at, bet.notes
        ])
        
        bet_id = cursor.fetchone()['bet_id']
        
        # If account_id provided, update balance and log transaction
        if bet.account_id:
            cursor.execute("""
                UPDATE bankroll_accounts
                SET current_balance = current_balance - %s
                WHERE account_id = %s
                RETURNING current_balance
            """, [bet.stake_amount, bet.account_id])
            
            balance_result = cursor.fetchone()
            
            if balance_result:
                cursor.execute("""
                    INSERT INTO bankroll_transactions (
                        account_id, user_id, bet_id, transaction_type, amount, balance_after, description
                    )
                    VALUES (%s, %s, %s, 'bet_placed', %s, %s, 'Bet placed')
                """, [bet.account_id, user_id, bet_id, -bet.stake_amount, balance_result['current_balance']])
        
        # Fetch created bet with player details
        cursor.execute("SELECT * FROM v_recent_bets WHERE bet_id = %s", [bet_id])
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        
        return result
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to create bet: {str(e)}")

@router.get("/bets", response_model=dict)
async def get_bets(
    user_id: int = Query(default=1),
    status: Optional[Literal["pending", "won", "lost", "push", "cancelled"]] = None,
    account_id: Optional[int] = None,
    bet_type: Optional[str] = None,
    market_key: Optional[str] = None,
    player_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    conn = Depends(get_db)
):
    """
    Get bets with filtering and pagination.
    
    **Use Case:** Bet history table with filters
    **Returns:** Paginated list of bets
    """
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM v_recent_bets WHERE user_id = %s"
    params = [user_id]
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if account_id:
        query += " AND account_id = %s"
        params.append(account_id)
    
    if bet_type:
        query += " AND bet_type = %s"
        params.append(bet_type)
    
    if market_key:
        query += " AND market_key = %s"
        params.append(market_key)
    
    if player_id:
        query += " AND player_id = %s"
        params.append(player_id)
    
    if start_date:
        query += " AND DATE(placed_at) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(placed_at) <= %s"
        params.append(end_date)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM ({query}) as filtered"
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Get paginated results
    query += " ORDER BY placed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, (page - 1) * limit])
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "bets": results
    }

@router.get("/bets/{bet_id}", response_model=Bet)
async def get_bet(
    bet_id: int,
    conn = Depends(get_db)
):
    """
    Get details of a specific bet.
    
    **Use Case:** View bet details
    **Returns:** Bet details
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM v_recent_bets WHERE bet_id = %s", [bet_id])
    result = cursor.fetchone()
    cursor.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Bet not found")
    
    return result

@router.put("/bets/{bet_id}", response_model=Bet)
async def update_bet(
    bet_id: int,
    bet_update: BetUpdate,
    conn = Depends(get_db)
):
    """
    Update bet details (before settling).
    
    **Use Case:** Correct bet entry errors
    **Returns:** Updated bet details
    """
    cursor = conn.cursor()
    
    try:
        # Build update query dynamically
        update_fields = []
        params = []
        
        if bet_update.account_id is not None:
            update_fields.append("account_id = %s")
            params.append(bet_update.account_id)
        
        if bet_update.market_key is not None:
            update_fields.append("market_key = %s")
            params.append(bet_update.market_key)
        
        if bet_update.bet_side is not None:
            update_fields.append("bet_side = %s")
            params.append(bet_update.bet_side)
        
        if bet_update.line_value is not None:
            update_fields.append("line_value = %s")
            params.append(bet_update.line_value)
        
        if bet_update.odds_american is not None:
            update_fields.append("odds_american = %s")
            params.append(bet_update.odds_american)
            # Recalculate potential payout
            cursor.execute("SELECT stake_amount FROM bets WHERE bet_id = %s", [bet_id])
            stake = cursor.fetchone()
            if stake:
                new_payout = calculate_payout(bet_update.odds_american, Decimal(str(stake['stake_amount'])))
                update_fields.append("potential_payout = %s")
                params.append(new_payout)
        
        if bet_update.stake_amount is not None:
            update_fields.append("stake_amount = %s")
            params.append(bet_update.stake_amount)
            # Recalculate potential payout
            cursor.execute("SELECT odds_american FROM bets WHERE bet_id = %s", [bet_id])
            odds = cursor.fetchone()
            if odds:
                new_payout = calculate_payout(odds['odds_american'], bet_update.stake_amount)
                update_fields.append("potential_payout = %s")
                params.append(new_payout)
        
        if bet_update.notes is not None:
            update_fields.append("notes = %s")
            params.append(bet_update.notes)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(bet_id)
        query = f"UPDATE bets SET {', '.join(update_fields)} WHERE bet_id = %s RETURNING bet_id"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        conn.commit()
        
        # Fetch updated bet
        cursor.execute("SELECT * FROM v_recent_bets WHERE bet_id = %s", [bet_id])
        updated_bet = cursor.fetchone()
        cursor.close()
        
        return updated_bet
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to update bet: {str(e)}")

@router.delete("/bets/{bet_id}")
async def delete_bet(
    bet_id: int,
    conn = Depends(get_db)
):
    """
    Delete a bet (only if pending).
    
    **Use Case:** Remove mistakenly entered bet
    **Returns:** Success message
    """
    cursor = conn.cursor()
    
    try:
        # Get bet details first
        cursor.execute("""
            SELECT bet_id, status, account_id, stake_amount
            FROM bets
            WHERE bet_id = %s
        """, [bet_id])
        
        bet = cursor.fetchone()
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        # Only allow deleting pending bets (or modify this logic as needed)
        if bet['status'] != 'pending':
            raise HTTPException(status_code=400, detail="Can only delete pending bets")
        
        # If bet was deducted from account, refund it
        if bet['account_id']:
            cursor.execute("""
                UPDATE bankroll_accounts
                SET current_balance = current_balance + %s
                WHERE account_id = %s
            """, [bet['stake_amount'], bet['account_id']])
        
        # Delete bet (transactions will cascade)
        cursor.execute("DELETE FROM bets WHERE bet_id = %s", [bet_id])
        
        conn.commit()
        cursor.close()
        
        return {"message": "Bet deleted successfully", "bet_id": bet_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete bet: {str(e)}")

@router.post("/bets/{bet_id}/settle", response_model=Bet)
async def settle_bet(
    bet_id: int,
    settlement: BetSettle,
    conn = Depends(get_db)
):
    """
    Settle a bet (mark as won/lost/push).
    
    **Use Case:** Mark bet result and update bankroll
    **Returns:** Settled bet details
    """
    cursor = conn.cursor()
    
    try:
        # Get bet details
        cursor.execute("""
            SELECT bet_id, user_id, account_id, stake_amount, potential_payout, status
            FROM bets
            WHERE bet_id = %s
        """, [bet_id])
        
        bet = cursor.fetchone()
        
        if not bet:
            raise HTTPException(status_code=404, detail="Bet not found")
        
        if bet['status'] != 'pending':
            raise HTTPException(status_code=400, detail="Bet already settled")
        
        # Calculate payout and profit/loss
        actual_payout = Decimal('0')
        profit_loss = Decimal('0')
        
        if settlement.status == 'won':
            actual_payout = bet['potential_payout']
            profit_loss = actual_payout - bet['stake_amount']
        elif settlement.status == 'lost':
            actual_payout = Decimal('0')
            profit_loss = -bet['stake_amount']
        elif settlement.status == 'push':
            actual_payout = bet['stake_amount']
            profit_loss = Decimal('0')
        elif settlement.status == 'cancelled':
            actual_payout = bet['stake_amount']
            profit_loss = Decimal('0')
        
        # Update bet
        cursor.execute("""
            UPDATE bets
            SET status = %s, actual_payout = %s, profit_loss = %s, settled_at = NOW()
            WHERE bet_id = %s
        """, [settlement.status, actual_payout, profit_loss, bet_id])
        
        # Update account balance if account exists
        if bet['account_id'] and actual_payout > 0:
            cursor.execute("""
                UPDATE bankroll_accounts
                SET current_balance = current_balance + %s
                WHERE account_id = %s
                RETURNING current_balance
            """, [actual_payout, bet['account_id']])
            
            balance_result = cursor.fetchone()
            
            if balance_result:
                # Log transaction
                cursor.execute("""
                    INSERT INTO bankroll_transactions (
                        account_id, user_id, bet_id, transaction_type, amount, balance_after, description
                    )
                    VALUES (%s, %s, %s, 'bet_settled', %s, %s, %s)
                """, [
                    bet['account_id'], bet['user_id'], bet_id, 
                    profit_loss, balance_result['current_balance'], 
                    f"Bet settled: {settlement.status}"
                ])
        
        conn.commit()
        
        # Fetch updated bet
        cursor.execute("SELECT * FROM v_recent_bets WHERE bet_id = %s", [bet_id])
        settled_bet = cursor.fetchone()
        cursor.close()
        
        return settled_bet
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to settle bet: {str(e)}")

# =========================================================
# ANALYTICS ENDPOINTS
# =========================================================

@router.get("/analytics/overview", response_model=BankrollOverview)
async def get_overview(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get complete bankroll overview for dashboard.
    
    **Use Case:** Main dashboard stats
    **Returns:** All key metrics
    """
    cursor = conn.cursor()
    
    # Get bankroll stats
    cursor.execute("""
        SELECT * FROM v_bankroll_overview WHERE user_id = %s
    """, [user_id])
    bankroll_stats = cursor.fetchone() or {
        'total_bankroll': 0, 'total_starting_balance': 0, 
        'total_profit_loss': 0, 'roi_percentage': 0
    }
    
    # Get bet stats
    cursor.execute("""
        SELECT * FROM v_bet_statistics WHERE user_id = %s
    """, [user_id])
    bet_stats = cursor.fetchone() or {
        'total_bets': 0, 'pending_bets': 0, 'won_bets': 0, 
        'lost_bets': 0, 'push_bets': 0, 'locked_in_bets': 0,
        'total_profit_loss': 0, 'win_rate': 0, 'avg_bet_size': 0
    }
    
    # Get current streak
    current_streak = get_current_streak(cursor, user_id)
    
    cursor.close()
    
    # Calculate available balance
    available_balance = Decimal(str(bankroll_stats['total_bankroll'])) - Decimal(str(bet_stats['locked_in_bets']))
    
    return {
        "total_bankroll": bankroll_stats['total_bankroll'],
        "available_balance": available_balance,
        "locked_in_bets": bet_stats['locked_in_bets'],
        "total_profit_loss": bet_stats['total_profit_loss'],
        "roi": bankroll_stats['roi_percentage'],
        "win_rate": bet_stats['win_rate'],
        "total_bets": bet_stats['total_bets'],
        "pending_bets": bet_stats['pending_bets'],
        "won_bets": bet_stats['won_bets'],
        "lost_bets": bet_stats['lost_bets'],
        "push_bets": bet_stats['push_bets'],
        "avg_bet_size": bet_stats['avg_bet_size'],
        "current_streak": current_streak
    }

@router.get("/analytics/chart-data", response_model=List[ChartDataPoint])
async def get_chart_data(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=1, le=365),
    conn = Depends(get_db)
):
    """
    Get bankroll history for charting.
    
    **Use Case:** Bankroll over time chart
    **Returns:** Daily balance snapshots
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH RECURSIVE date_series AS (
            SELECT CURRENT_DATE - INTERVAL '1 day' * (%s - 1) as date
            UNION ALL
            SELECT date + INTERVAL '1 day'
            FROM date_series
            WHERE date < CURRENT_DATE
        ),
        daily_balance AS (
            SELECT 
                ds.date,
                COALESCE(SUM(ba.starting_balance), 0) as starting_balance,
                COALESCE(SUM(
                    CASE 
                        WHEN bt.transaction_type = 'bet_settled' AND bt.amount > 0 THEN bt.amount
                        WHEN bt.transaction_type = 'bet_placed' THEN bt.amount
                        ELSE 0
                    END
                ) FILTER (WHERE DATE(bt.created_at) <= ds.date), 0) as cumulative_change
            FROM date_series ds
            LEFT JOIN bankroll_accounts ba ON ba.user_id = %s
            LEFT JOIN bankroll_transactions bt ON bt.user_id = %s
            GROUP BY ds.date
        )
        SELECT 
            TO_CHAR(date, 'YYYY-MM-DD') as date,
            starting_balance + cumulative_change as balance,
            cumulative_change as profit_loss
        FROM daily_balance
        ORDER BY date
    """, [days, user_id, user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

@router.get("/analytics/by-bookmaker", response_model=List[BookmakerPerformance])
async def get_bookmaker_performance(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get performance breakdown by sportsbook.
    
    **Use Case:** Compare bookmaker profitability
    **Returns:** Stats per bookmaker
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM v_performance_by_bookmaker 
        WHERE user_id = %s
        ORDER BY total_profit_loss DESC
    """, [user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

@router.get("/analytics/by-market", response_model=List[MarketPerformance])
async def get_market_performance(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get performance breakdown by market type.
    
    **Use Case:** Identify best/worst bet types
    **Returns:** Stats per market
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM v_performance_by_market 
        WHERE user_id = %s
        ORDER BY total_profit_loss DESC
    """, [user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

# =========================================================
# TRANSACTIONS ENDPOINT
# =========================================================

@router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    user_id: int = Query(default=1),
    account_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    conn = Depends(get_db)
):
    """
    Get transaction history.
    
    **Use Case:** View all account activity
    **Returns:** List of transactions
    """
    cursor = conn.cursor()
    
    query = """
        SELECT transaction_id, account_id, user_id, bet_id, transaction_type, 
               amount, balance_after, description, created_at
        FROM bankroll_transactions
        WHERE user_id = %s
    """
    params = [user_id]
    
    if account_id:
        query += " AND account_id = %s"
        params.append(account_id)
    
    if transaction_type:
        query += " AND transaction_type = %s"
        params.append(transaction_type)
    
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return results
