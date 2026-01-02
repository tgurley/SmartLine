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

16. POST /bankroll/parlays - Create parlay
17. GET /bankroll/parlays - List parlays
18. GET /bankroll/parlays/{parlay_id} - Get single parlay
19. POST /bankroll/parlays/{parlay_id}/settle - Settle parlay
20. DELETE /bankroll/parlays/{parlay_id} - Delete pending parlay

21. GET /bankroll/analytics/by-sport - Performance per sport
22. GET /bankroll/analytics/parlay-stats - Parlay analytics
23. GET /bankroll/analytics/sport-trends - Daily trends by sport
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
class Alert(BaseModel):
    alert_id: int
    user_id: int
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime

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
    avg_bet_size: Decimal = Field(decimal_places=2)
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

class GoalCreate(BaseModel):
    goal_type: Literal['daily', 'weekly', 'monthly', 'yearly']
    goal_amount: Decimal = Field(..., gt=0)
    start_date: date
    end_date: date
    description: Optional[str] = None

class GoalUpdate(BaseModel):
    goal_amount: Optional[Decimal] = Field(None, gt=0)
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: Optional[Literal['active', 'completed', 'failed']] = None
    
# =========================================================
# PARLAY MODELS
# =========================================================

class ParlayLeg(BaseModel):
    """Single leg of a parlay"""
    bet_type: str
    sport: str = "NFL"
    market_key: str
    bet_side: Optional[str] = None
    line_value: Optional[float] = None
    odds_american: int
    
    # Optional references
    game_id: Optional[int] = None
    player_id: Optional[int] = None
    sport_id: Optional[int] = None
    notes: Optional[str] = None


class ParlayCreate(BaseModel):
    """Create a new parlay"""
    account_id: int
    legs: List[ParlayLeg]  # 2-15 legs
    stake_amount: float
    notes: Optional[str] = None


class ParlayResponse(BaseModel):
    """Parlay with calculated fields"""
    parlay_id: int
    user_id: int
    account_id: int
    bookmaker_name: Optional[str]
    total_legs: int
    combined_odds_american: int
    stake_amount: float
    potential_payout: float
    actual_payout: Optional[float]
    profit_loss: Optional[float]
    sport_mix: str
    status: str
    placed_at: datetime
    settled_at: Optional[datetime]
    legs_won: int
    legs_lost: int
    legs_pending: int
    legs: List[dict]

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
# PARLAY HELPER FUNCTIONS
# =========================================================

def calculate_parlay_odds(legs: List[ParlayLeg]) -> int:
    """
    Calculate combined American odds for a parlay.
    
    Formula:
    1. Convert each American odds to decimal
    2. Multiply all decimal odds together
    3. Convert back to American odds
    """
    decimal_odds = []
    
    for leg in legs:
        if leg.odds_american > 0:
            # Positive odds: (odds / 100) + 1
            decimal = (leg.odds_american / 100) + 1
        else:
            # Negative odds: (100 / abs(odds)) + 1
            decimal = (100 / abs(leg.odds_american)) + 1
        
        decimal_odds.append(decimal)
    
    # Multiply all decimal odds
    combined_decimal = 1.0
    for odds in decimal_odds:
        combined_decimal *= odds
    
    # Convert back to American
    if combined_decimal >= 2.0:
        # Positive odds: (decimal - 1) * 100
        american = int((combined_decimal - 1) * 100)
    else:
        # Negative odds: -100 / (decimal - 1)
        american = int(-100 / (combined_decimal - 1))
    
    return american


def calculate_parlay_payout(stake: float, american_odds: int) -> float:
    """Calculate parlay payout from American odds"""
    if american_odds > 0:
        return stake * (1 + american_odds / 100)
    else:
        return stake * (1 + 100 / abs(american_odds))


def get_sport_mix(legs: List[ParlayLeg]) -> str:
    """Get unique sports in parlay"""
    sports = sorted(set(leg.sport for leg in legs))
    if len(sports) == 1:
        return sports[0]
    else:
        return "+".join(sports)

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
        
        # Check and create alerts after settling
        check_and_create_alerts(cursor, bet['user_id'], bet_id, conn)
        
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
    days: int = Query(default=30, ge=1, le=365),
    conn = Depends(get_db)
):
    """
    Get complete bankroll overview for dashboard.
    
    **Use Case:** Main dashboard stats
    **Returns:** All key metrics filtered by date range
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM v_bankroll_overview WHERE user_id = %s
    """, [user_id])
    bankroll_stats = cursor.fetchone() or {
        'total_bankroll': 0, 'total_starting_balance': 0, 
        'total_profit_loss': 0, 'roi_percentage': 0
    }
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bets,
            COUNT(*) FILTER (WHERE status = 'pending') as pending_bets,
            COUNT(*) FILTER (WHERE status = 'won') as won_bets,
            COUNT(*) FILTER (WHERE status = 'lost') as lost_bets,
            COUNT(*) FILTER (WHERE status = 'push') as push_bets,
            COALESCE(SUM(stake_amount) FILTER (WHERE status = 'pending'), 0) as locked_in_bets,
            COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
            ROUND(
                CASE 
                    WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                        (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                         COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                    ELSE 0
                END,
            1) as win_rate,
            ROUND(COALESCE(AVG(stake_amount), 0), 2) as avg_bet_size
        FROM bets
        WHERE user_id = %s
        AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
    """, [user_id, days])
    
    bet_stats = cursor.fetchone() or {
        'total_bets': 0, 'pending_bets': 0, 'won_bets': 0, 
        'lost_bets': 0, 'push_bets': 0, 'locked_in_bets': 0,
        'total_profit_loss': 0, 'win_rate': 0, 'avg_bet_size': 0
    }
    
    cursor.execute("""
        WITH recent_bets AS (
            SELECT status, settled_at
            FROM bets
            WHERE user_id = %s
            AND status IN ('won', 'lost')
            AND settled_at IS NOT NULL
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY settled_at DESC
            LIMIT 20
        ),
        streak_calc AS (
            SELECT 
                status,
                COUNT(*) as streak_length,
                ROW_NUMBER() OVER (ORDER BY MIN(settled_at) DESC) as streak_num
            FROM (
                SELECT 
                    status,
                    settled_at,
                    ROW_NUMBER() OVER (ORDER BY settled_at DESC) - 
                    ROW_NUMBER() OVER (PARTITION BY status ORDER BY settled_at DESC) as grp
                FROM recent_bets
            ) grouped
            GROUP BY status, grp
        )
        SELECT status, streak_length
        FROM streak_calc
        WHERE streak_num = 1
    """, [user_id, days])
    
    current_streak = cursor.fetchone()
    
    cursor.close()
    
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
        "avg_bet_size": round(Decimal(str(bet_stats['avg_bet_size'])), 2),
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
            -- Generate date range
            SELECT CURRENT_DATE - INTERVAL '1 day' * (%s - 1) as date
            UNION ALL
            SELECT date + INTERVAL '1 day'
            FROM date_series
            WHERE date < CURRENT_DATE
        ),
        account_starting_balance AS (
            -- Get the TOTAL starting balance across all accounts (calculated once)
            SELECT COALESCE(SUM(starting_balance), 0) as total_starting
            FROM bankroll_accounts
            WHERE user_id = %s
        ),
        daily_pl AS (
            -- Calculate cumulative profit/loss from settled bets only
            SELECT 
                ds.date,
                COALESCE(SUM(b.profit_loss) FILTER (
                    WHERE DATE(b.settled_at) <= ds.date 
                    AND b.status IN ('won', 'lost', 'push')
                ), 0) as cumulative_pl
            FROM date_series ds
            LEFT JOIN bets b ON b.user_id = %s
            GROUP BY ds.date
        )
        SELECT 
            TO_CHAR(dpl.date, 'YYYY-MM-DD') as date,
            asb.total_starting + dpl.cumulative_pl as balance,
            dpl.cumulative_pl as profit_loss
        FROM daily_pl dpl
        CROSS JOIN account_starting_balance asb
        ORDER BY dpl.date
    """, [days, user_id, user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

@router.get("/analytics/by-bookmaker", response_model=List[BookmakerPerformance])
async def get_bookmaker_performance(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=1, le=365),
    conn = Depends(get_db)
):
    """
    Get performance breakdown by sportsbook.
    
    **Use Case:** Compare bookmaker profitability
    **Returns:** Stats per bookmaker filtered by date range
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ba.bookmaker_name,
            COUNT(b.bet_id) as total_bets,
            COUNT(b.bet_id) FILTER (WHERE b.status = 'won') as won_bets,
            COUNT(b.bet_id) FILTER (WHERE b.status = 'lost') as lost_bets,
            ROUND(
                CASE 
                    WHEN COUNT(b.bet_id) FILTER (WHERE b.status IN ('won', 'lost')) > 0 THEN
                        (COUNT(b.bet_id) FILTER (WHERE b.status = 'won')::numeric / 
                         COUNT(b.bet_id) FILTER (WHERE b.status IN ('won', 'lost')) * 100)
                    ELSE 0
                END,
            1) as win_rate,
            COALESCE(SUM(b.profit_loss) FILTER (WHERE b.status IN ('won', 'lost', 'push')), 0) as total_profit_loss
        FROM bankroll_accounts ba
        LEFT JOIN bets b ON ba.account_id = b.account_id 
            AND b.placed_at >= CURRENT_DATE - INTERVAL '%s days'
        WHERE ba.user_id = %s
        GROUP BY ba.bookmaker_name
        HAVING COUNT(b.bet_id) > 0
        ORDER BY total_profit_loss DESC
    """, [days, user_id])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results

@router.get("/analytics/by-market", response_model=List[MarketPerformance])
async def get_market_performance(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=1, le=365),
    conn = Depends(get_db)
):
    """
    Get performance breakdown by market type.
    
    **Use Case:** Identify best/worst bet types
    **Returns:** Stats per market filtered by date range
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            market_key,
            COUNT(*) as total_bets,
            COUNT(*) FILTER (WHERE status = 'won') as won_bets,
            COUNT(*) FILTER (WHERE status = 'lost') as lost_bets,
            ROUND(
                CASE 
                    WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                        (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                         COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                    ELSE 0
                END,
            1) as win_rate,
            COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
            ROUND(COALESCE(AVG(stake_amount), 0), 2) as avg_stake
        FROM bets
        WHERE user_id = %s
        AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
        AND market_key IS NOT NULL
        GROUP BY market_key
        ORDER BY total_profit_loss DESC
    """, [user_id, days])
    
    results = cursor.fetchall()
    cursor.close()
    
    return results
    
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

@router.post("/goals")
async def create_goal(
    goal_data: GoalCreate,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Create a new profit goal.
    
    **Use Case:** Goal creation from dashboard
    **Returns:** Created goal with ID
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_goals (
                user_id, goal_type, goal_amount, 
                start_date, end_date, description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING goal_id, user_id, goal_type, goal_amount, 
                      start_date, end_date, status, description, 
                      created_at, completed_at
        ''', [
            user_id, 
            goal_data.goal_type, 
            goal_data.goal_amount, 
            goal_data.start_date, 
            goal_data.end_date, 
            goal_data.description
        ])
        
        goal = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return goal
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")

@router.get("/goals")
async def get_goals(
    user_id: int = Query(default=1),
    status: str = Query(default='active'),
    conn = Depends(get_db)
):
    """
    Get user goals with progress.
    
    **Use Case:** Goals dashboard
    **Returns:** List of goals with progress
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM v_goal_progress
            WHERE user_id = %s
            AND (%s = 'all' OR status = %s)
            ORDER BY 
                CASE status
                    WHEN 'active' THEN 1
                    WHEN 'completed' THEN 2
                    WHEN 'failed' THEN 3
                END,
                end_date DESC
        ''', [user_id, status, status])
        
        goals = cursor.fetchall()
        cursor.close()
        
        return goals
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get goals: {str(e)}")

@router.get("/goals/{goal_id}")
async def get_goal(
    goal_id: int,
    conn = Depends(get_db)
):
    """
    Get a single goal with progress.
    
    **Use Case:** Goal details
    **Returns:** Goal with current progress
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM v_goal_progress
            WHERE goal_id = %s
        ''', [goal_id])
        
        goal = cursor.fetchone()
        cursor.close()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        return goal
        
    except HTTPException:
        raise
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get goal: {str(e)}")

@router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    conn = Depends(get_db)
):
    """
    Update a goal.
    
    **Use Case:** Edit goal details
    **Returns:** Updated goal
    """
    cursor = conn.cursor()
    
    try:
        update_fields = []
        params = []
        
        if goal_data.goal_amount is not None:
            update_fields.append("goal_amount = %s")
            params.append(goal_data.goal_amount)
        
        if goal_data.end_date is not None:
            update_fields.append("end_date = %s")
            params.append(goal_data.end_date)
        
        if goal_data.description is not None:
            update_fields.append("description = %s")
            params.append(goal_data.description)
        
        if goal_data.status is not None:
            update_fields.append("status = %s")
            params.append(goal_data.status)
            
            if goal_data.status == 'completed':
                update_fields.append("completed_at = NOW()")
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(goal_id)
        query = f"""
            UPDATE user_goals 
            SET {', '.join(update_fields)}
            WHERE goal_id = %s
            RETURNING goal_id, user_id, goal_type, goal_amount, 
                      start_date, end_date, status, description, 
                      created_at, completed_at
        """
        
        cursor.execute(query, params)
        goal = cursor.fetchone()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        conn.commit()
        cursor.close()
        
        return goal
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: int,
    conn = Depends(get_db)
):
    """
    Delete a goal.
    
    **Use Case:** Remove unwanted goal
    **Returns:** Success message
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM user_goals
            WHERE goal_id = %s
            RETURNING goal_id
        ''', [goal_id])
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        conn.commit()
        cursor.close()
        
        return {"message": "Goal deleted successfully", "goal_id": goal_id}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")

@router.get("/analytics/time-analysis")
async def get_time_analysis(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=7, le=365),
    conn = Depends(get_db)
):
    '''
    Analyze betting performance by day of week and time of day.
    
    **Use Case:** Time Analysis section
    **Returns:** Performance breakdown by day/time
    '''
    cursor = conn.cursor()
    
    try:
        # Performance by day of week
        cursor.execute('''
            SELECT 
                EXTRACT(DOW FROM placed_at) as day_of_week,
                CASE EXTRACT(DOW FROM placed_at)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_name,
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE status = 'won') as wins,
                COUNT(*) FILTER (WHERE status = 'lost') as losses,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
                COALESCE(SUM(stake_amount), 0) as total_staked
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY EXTRACT(DOW FROM placed_at)
            ORDER BY day_of_week
        ''', [user_id, days])
        
        day_of_week_data = cursor.fetchall()
        
        # Performance by time of day
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 'Morning'
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 'Afternoon'
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 'Evening'
                    ELSE 'Late Night'
                END as time_period,
                CASE 
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 1
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 2
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 3
                    ELSE 4
                END as period_order,
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE status = 'won') as wins,
                COUNT(*) FILTER (WHERE status = 'lost') as losses,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
                COALESCE(SUM(stake_amount), 0) as total_staked
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY 
                CASE 
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 'Morning'
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 'Afternoon'
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 'Evening'
                    ELSE 'Late Night'
                END,
                CASE 
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 1
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 2
                    WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 3
                    ELSE 4
                END
            ORDER BY period_order
        ''', [user_id, days])
        
        time_of_day_data = cursor.fetchall()
        
        # Best day/time insights
        cursor.execute('''
            WITH day_performance AS (
                SELECT 
                    CASE EXTRACT(DOW FROM placed_at)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_name,
                    COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                    COUNT(*) as bet_count
                FROM bets
                WHERE user_id = %s
                AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY EXTRACT(DOW FROM placed_at)
            )
            SELECT day_name, profit_loss, bet_count
            FROM day_performance
            WHERE bet_count >= 3  -- At least 3 bets for statistical relevance
            ORDER BY profit_loss DESC
            LIMIT 1
        ''', [user_id, days])
        
        best_day = cursor.fetchone()
        
        cursor.execute('''
            WITH time_performance AS (
                SELECT 
                    CASE 
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 'Morning'
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 'Afternoon'
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 'Evening'
                        ELSE 'Late Night'
                    END as time_period,
                    COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                    COUNT(*) as bet_count
                FROM bets
                WHERE user_id = %s
                AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY 
                    CASE 
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 6 AND 11 THEN 'Morning'
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 12 AND 17 THEN 'Afternoon'
                        WHEN EXTRACT(HOUR FROM placed_at) BETWEEN 18 AND 23 THEN 'Evening'
                        ELSE 'Late Night'
                    END
            )
            SELECT time_period, profit_loss, bet_count
            FROM time_performance
            WHERE bet_count >= 3
            ORDER BY profit_loss DESC
            LIMIT 1
        ''', [user_id, days])
        
        best_time = cursor.fetchone()
        
        cursor.close()
        
        return {
            "by_day_of_week": day_of_week_data,
            "by_time_of_day": time_of_day_data,
            "insights": {
                "best_day": best_day,
                "best_time": best_time
            }
        }
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get time analysis: {str(e)}")

@router.get("/analytics/market-deep-dive")
async def get_market_deep_dive(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=7, le=365),
    conn = Depends(get_db)
):
    '''
    Detailed market performance analysis.
    
    **Use Case:** Market Performance section
    **Returns:** Comprehensive market statistics
    '''
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                market_key,
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_bets,
                COUNT(*) FILTER (WHERE status = 'won') as won_bets,
                COUNT(*) FILTER (WHERE status = 'lost') as lost_bets,
                COUNT(*) FILTER (WHERE status = 'push') as push_bets,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate,
                COALESCE(SUM(stake_amount), 0) as total_staked,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
                ROUND(
                    CASE 
                        WHEN SUM(stake_amount) > 0 THEN
                            (SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push'))::numeric / 
                             SUM(stake_amount) * 100)
                        ELSE 0
                    END,
                1) as roi,
                ROUND(AVG(stake_amount), 2) as avg_stake,
                ROUND(
                    AVG(profit_loss) FILTER (WHERE status = 'won'),
                2) as avg_win_amount,
                ROUND(
                    AVG(profit_loss) FILTER (WHERE status = 'lost'),
                2) as avg_loss_amount
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            AND market_key IS NOT NULL
            GROUP BY market_key
            ORDER BY total_profit_loss DESC
        ''', [user_id, days])
        
        markets = cursor.fetchall()
        
        # Get best/worst markets
        cursor.execute('''
            WITH market_stats AS (
                SELECT 
                    market_key,
                    COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                    COUNT(*) as bet_count
                FROM bets
                WHERE user_id = %s
                AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
                AND market_key IS NOT NULL
                GROUP BY market_key
            )
            SELECT market_key, profit_loss, bet_count
            FROM market_stats
            WHERE bet_count >= 3
            AND profit_loss > 0  -- Only positive P/L
            ORDER BY profit_loss DESC
            LIMIT 3
        ''', [user_id, days])
        
        best_markets = cursor.fetchall()
        
        cursor.execute('''
            WITH market_stats AS (
                SELECT 
                    market_key,
                    COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                    COUNT(*) as bet_count
                FROM bets
                WHERE user_id = %s
                AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
                AND market_key IS NOT NULL
                GROUP BY market_key
            )
            SELECT market_key, profit_loss, bet_count
            FROM market_stats
            WHERE bet_count >= 3
            AND profit_loss < 0  -- Only negative P/L
            ORDER BY profit_loss ASC
            LIMIT 3
        ''', [user_id, days])
        
        worst_markets = cursor.fetchall()
        
        cursor.close()
        
        return {
            "markets": markets,
            "best_markets": best_markets,
            "worst_markets": worst_markets
        }
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get market analysis: {str(e)}")

@router.get("/analytics/insights")
async def get_insights(
    user_id: int = Query(default=1),
    days: int = Query(default=30, ge=7, le=365),
    conn = Depends(get_db)
):
    '''
    Generate AI-like insights and recommendations.
    
    **Use Case:** Insights section
    **Returns:** Array of actionable insights
    '''
    cursor = conn.cursor()
    insights = []
    
    try:
        # Get overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE status = 'won') as wins,
                COUNT(*) FILTER (WHERE status = 'lost') as losses,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as total_pl,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
        ''', [user_id, days])
        
        overall = cursor.fetchone()
        
        # Insight 1: Overall performance
        if overall['total_bets'] > 0:
            if float(overall['total_pl']) > 0:
                insights.append({
                    "type": "success",
                    "icon": "trending-up",
                    "title": "Profitable Period",
                    "message": f"You're up ${abs(float(overall['total_pl'])):.2f} over the last {days} days with a {overall['win_rate']}% win rate.",
                    "priority": 1
                })
            elif float(overall['total_pl']) < 0:
                insights.append({
                    "type": "warning",
                    "icon": "trending-down",
                    "title": "Negative Trend",
                    "message": f"You're down ${abs(float(overall['total_pl'])):.2f} over the last {days} days. Consider reviewing your strategy.",
                    "priority": 1
                })
        
        # Insight 2: Current streak
        cursor.execute('''
            WITH recent_bets AS (
                SELECT status, settled_at
                FROM bets
                WHERE user_id = %s
                AND status IN ('won', 'lost')
                AND settled_at IS NOT NULL
                ORDER BY settled_at DESC
                LIMIT 10
            ),
            streak_calc AS (
                SELECT 
                    status,
                    COUNT(*) as streak_length,
                    ROW_NUMBER() OVER (ORDER BY MIN(settled_at) DESC) as streak_num
                FROM (
                    SELECT 
                        status,
                        settled_at,
                        ROW_NUMBER() OVER (ORDER BY settled_at DESC) - 
                        ROW_NUMBER() OVER (PARTITION BY status ORDER BY settled_at DESC) as grp
                    FROM recent_bets
                ) grouped
                GROUP BY status, grp
            )
            SELECT status, streak_length
            FROM streak_calc
            WHERE streak_num = 1
        ''', [user_id])
        
        streak = cursor.fetchone()
        
        if streak and streak['streak_length'] >= 3:
            if streak['status'] == 'won':
                insights.append({
                    "type": "success",
                    "icon": "fire",
                    "title": f"🔥 Hot Streak!",
                    "message": f"You're on a {streak['streak_length']}-win streak. Stay focused!",
                    "priority": 2
                })
            else:
                insights.append({
                    "type": "warning",
                    "icon": "alert-triangle",
                    "title": "Losing Streak",
                    "message": f"You've lost {streak['streak_length']} in a row. Consider taking a break or reducing stake sizes.",
                    "priority": 2
                })
        
        # Insight 3: Best day of week
        cursor.execute('''
            SELECT 
                CASE EXTRACT(DOW FROM placed_at)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_name,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                COUNT(*) as bet_count,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY EXTRACT(DOW FROM placed_at)
            HAVING COUNT(*) >= 3
            ORDER BY profit_loss DESC
            LIMIT 1
        ''', [user_id, days])
        
        best_day = cursor.fetchone()
        
        if best_day:
            insights.append({
                "type": "info",
                "icon": "calendar",
                "title": f"Best Day: {best_day['day_name']}",
                "message": f"You're most profitable on {best_day['day_name']}s with ${float(best_day['profit_loss']):.2f} profit and {best_day['win_rate']}% win rate.",
                "priority": 3
            })
        
        # Insight 4: Worst day of week
        cursor.execute('''
            SELECT 
                CASE EXTRACT(DOW FROM placed_at)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_name,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                COUNT(*) as bet_count
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY EXTRACT(DOW FROM placed_at)
            HAVING COUNT(*) >= 3
            ORDER BY profit_loss ASC
            LIMIT 1
        ''', [user_id, days])
        
        worst_day = cursor.fetchone()
        
        if worst_day and float(worst_day['profit_loss']) < 0:
            insights.append({
                "type": "warning",
                "icon": "alert-circle",
                "title": f"Avoid {worst_day['day_name']}s",
                "message": f"You tend to lose on {worst_day['day_name']}s (${abs(float(worst_day['profit_loss'])):.2f} loss). Consider sitting out.",
                "priority": 4
            })
        
        # Insight 5: Best market
        cursor.execute('''
            SELECT 
                market_key,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                COUNT(*) as bet_count,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END, 
                1) as win_rate
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
            AND market_key IS NOT NULL
            GROUP BY market_key
            HAVING COUNT(*) >= 5
            ORDER BY profit_loss DESC
            LIMIT 1
        ''', [user_id, days])
        
        best_market = cursor.fetchone()
        
        if best_market:
            market_name = {
                'player_pass_yds': 'Pass Yards',
                'player_rush_yds': 'Rush Yards',
                'player_reception_yds': 'Receiving Yards',
                'player_pass_tds': 'Pass TDs',
                'player_anytime_td': 'Anytime TD'
            }.get(best_market['market_key'], best_market['market_key'])
            
            insights.append({
                "type": "success",
                "icon": "target",
                "title": f"Strong Market: {market_name}",
                "message": f"Your best market with ${float(best_market['profit_loss']):.2f} profit and {best_market['win_rate']}% win rate.",
                "priority": 5
            })
        
        # Insight 6: Unit size recommendation
        cursor.execute('''
            SELECT COALESCE(SUM(current_balance), 0) as total_bankroll
            FROM bankroll_accounts
            WHERE user_id = %s
        ''', [user_id])
        
        bankroll = cursor.fetchone()
        
        cursor.execute('''
            SELECT ROUND(AVG(stake_amount), 2) as avg_stake
            FROM bets
            WHERE user_id = %s
            AND placed_at >= CURRENT_DATE - INTERVAL '%s days'
        ''', [user_id, days])
        
        avg_stake = cursor.fetchone()
        
        if bankroll and avg_stake and float(bankroll['total_bankroll']) > 0:
            stake_percentage = (float(avg_stake['avg_stake']) / float(bankroll['total_bankroll'])) * 100
            
            if stake_percentage > 5:
                insights.append({
                    "type": "warning",
                    "icon": "alert-triangle",
                    "title": "High Risk",
                    "message": f"Your average bet (${avg_stake['avg_stake']}) is {stake_percentage:.1f}% of your bankroll. Consider reducing to 1-3% for better risk management.",
                    "priority": 6
                })
            elif stake_percentage < 1:
                insights.append({
                    "type": "info",
                    "icon": "shield",
                    "title": "Conservative Betting",
                    "message": f"Your average bet is only {stake_percentage:.1f}% of bankroll. You're betting very conservatively.",
                    "priority": 6
                })
        
        # Insight 7: Recent trend
        cursor.execute('''
            WITH recent_performance AS (
                SELECT 
                    DATE(settled_at) as bet_date,
                    SUM(profit_loss) as daily_pl
                FROM bets
                WHERE user_id = %s
                AND settled_at >= CURRENT_DATE - INTERVAL '7 days'
                AND status IN ('won', 'lost', 'push')
                GROUP BY DATE(settled_at)
                ORDER BY bet_date DESC
            )
            SELECT 
                CASE 
                    WHEN COUNT(*) FILTER (WHERE daily_pl > 0) > COUNT(*) FILTER (WHERE daily_pl < 0) THEN 'improving'
                    WHEN COUNT(*) FILTER (WHERE daily_pl < 0) > COUNT(*) FILTER (WHERE daily_pl > 0) THEN 'declining'
                    ELSE 'stable'
                END as trend
            FROM recent_performance
        ''', [user_id])
        
        trend = cursor.fetchone()
        
        if trend:
            if trend['trend'] == 'improving':
                insights.append({
                    "type": "success",
                    "icon": "trending-up",
                    "title": "Positive Momentum",
                    "message": "Your performance is trending upward over the last week. Keep it up!",
                    "priority": 7
                })
            elif trend['trend'] == 'declining':
                insights.append({
                    "type": "warning",
                    "icon": "trending-down",
                    "title": "Declining Performance",
                    "message": "Your performance has declined over the last week. Consider reviewing your recent bets.",
                    "priority": 7
                })
        
        cursor.close()
        
        # Sort by priority
        insights.sort(key=lambda x: x['priority'])
        
        return {
            "insights": insights,
            "generated_at": "now"
        }
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")
    
@router.get("/alerts")
async def get_alerts(
    user_id: int = Query(default=1),
    read: str = Query(default='false'),
    limit: int = Query(default=50, le=100),
    conn = Depends(get_db)
):
    """
    Get user alerts.
    
    **Use Case:** Alert center dropdown
    **Returns:** List of alerts
    """
    cursor = conn.cursor()
    
    try:
        if read == 'all':
            cursor.execute('''
                SELECT * FROM user_alerts
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', [user_id, limit])
        else:
            cursor.execute('''
                SELECT * FROM user_alerts
                WHERE user_id = %s
                AND is_read = FALSE
                ORDER BY created_at DESC
                LIMIT %s
            ''', [user_id, limit])
        
        alerts = cursor.fetchall()
        cursor.close()
        
        return alerts
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/alerts/unread-count")
async def get_unread_count(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get count of unread alerts.
    
    **Use Case:** Notification badge
    **Returns:** Unread count
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM user_alerts
            WHERE user_id = %s
            AND is_read = FALSE
        ''', [user_id])
        
        result = cursor.fetchone()
        cursor.close()
        
        return {"count": result['count'] if result else 0}
        
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")

@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    conn = Depends(get_db)
):
    """
    Mark an alert as read.
    
    **Use Case:** Dismiss notification
    **Returns:** Updated alert
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_alerts
            SET is_read = TRUE
            WHERE alert_id = %s
            RETURNING *
        ''', [alert_id])
        
        alert = cursor.fetchone()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        conn.commit()
        cursor.close()
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to mark alert as read: {str(e)}")

@router.put("/alerts/mark-all-read")
async def mark_all_read(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Mark all alerts as read.
    
    **Use Case:** Clear all notifications
    **Returns:** Count of updated alerts
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_alerts
            SET is_read = TRUE
            WHERE user_id = %s
            AND is_read = FALSE
            RETURNING alert_id
        ''', [user_id])
        
        updated = cursor.fetchall()
        count = len(updated)
        
        conn.commit()
        cursor.close()
        
        return {"message": f"Marked {count} alerts as read", "count": count}
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to mark all as read: {str(e)}")

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    conn = Depends(get_db)
):
    """
    Delete an alert.
    
    **Use Case:** Dismiss notification permanently
    **Returns:** Success message
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM user_alerts
            WHERE alert_id = %s
            RETURNING alert_id
        ''', [alert_id])
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        conn.commit()
        cursor.close()
        
        return {"message": "Alert deleted successfully", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")

# =========================================================
# ALERT GENERATION HELPER FUNCTIONS
# =========================================================

def check_and_create_alerts(cursor, user_id, bet_id, conn):
    """
    Check for conditions that should trigger alerts and create them.
    Call this function after settling a bet.
    """
    try:
        # Get user settings
        cursor.execute('''
            SELECT * FROM bankroll_settings WHERE user_id = %s
        ''', [user_id])
        settings = cursor.fetchone()
        
        if not settings:
            return
        
        # Check for streaks
        check_streak_alerts(cursor, user_id, settings, conn)
        
        # Check for limit warnings
        check_limit_alerts(cursor, user_id, settings, conn)
        
        # Check for goal achievements
        check_goal_alerts(cursor, user_id, conn)
    except Exception as e:
        # Don't fail bet settlement if alerts fail
        print(f"Alert generation error: {e}")

def check_streak_alerts(cursor, user_id, settings, conn):
    """Check for winning/losing streaks"""
    try:
        if not settings.get('enable_streak_alerts'):
            return
        
        # Get recent streak
        cursor.execute('''
            WITH recent_bets AS (
                SELECT status, settled_at
                FROM bets
                WHERE user_id = %s
                AND status IN ('won', 'lost')
                AND settled_at IS NOT NULL
                ORDER BY settled_at DESC
                LIMIT 10
            ),
            streak_calc AS (
                SELECT 
                    status,
                    COUNT(*) as streak_length,
                    ROW_NUMBER() OVER (ORDER BY MIN(settled_at) DESC) as streak_num
                FROM (
                    SELECT 
                        status,
                        settled_at,
                        ROW_NUMBER() OVER (ORDER BY settled_at DESC) - 
                        ROW_NUMBER() OVER (PARTITION BY status ORDER BY settled_at DESC) as grp
                    FROM recent_bets
                ) grouped
                GROUP BY status, grp
            )
            SELECT status, streak_length
            FROM streak_calc
            WHERE streak_num = 1
        ''', [user_id])
        
        streak = cursor.fetchone()
        
        if not streak:
            return
        
        # Alert on 3+ losing streak
        if streak['status'] == 'lost' and int(streak['streak_length']) >= 3:
            create_alert(
                cursor, user_id,
                'losing_streak',
                f"⚠️ You're on a {streak['streak_length']}-bet losing streak. Consider taking a break.",
                conn
            )
        
        # Alert on 5+ winning streak
        elif streak['status'] == 'won' and int(streak['streak_length']) >= 5:
            create_alert(
                cursor, user_id,
                'winning_streak',
                f"🔥 Amazing! You're on a {streak['streak_length']}-bet winning streak!",
                conn
            )
    except Exception as e:
        print(f"Streak alert error: {e}")

def check_limit_alerts(cursor, user_id, settings, conn):
    """Check if approaching betting limits"""
    try:
        if not settings.get('enable_limit_alerts'):
            return
        
        threshold = float(settings.get('alert_threshold_percentage', 80)) / 100
        
        # Check daily limit
        cursor.execute('''
            SELECT COALESCE(SUM(stake_amount), 0) as daily_total
            FROM bets
            WHERE user_id = %s
            AND DATE(placed_at) = CURRENT_DATE
        ''', [user_id])
        
        result = cursor.fetchone()
        if not result:
            return
            
        daily_total = float(result['daily_total'])
        daily_limit = float(settings.get('daily_limit', 0))
        
        if daily_limit > 0 and daily_total >= (daily_limit * threshold):
            percentage = (daily_total / daily_limit) * 100
            create_alert(
                cursor, user_id,
                'limit_warning',
                f"⚠️ You've used {percentage:.0f}% of your daily betting limit (${daily_total:.2f} / ${daily_limit:.2f})",
                conn
            )
    except Exception as e:
        print(f"Limit alert error: {e}")

def check_goal_alerts(cursor, user_id, conn):
    """Check for goal achievements"""
    try:
        cursor.execute('''
            SELECT * FROM v_goal_progress
            WHERE user_id = %s
            AND status = 'active'
            AND progress_percentage >= 100
        ''', [user_id])
        
        achieved_goals = cursor.fetchall()
        
        for goal in achieved_goals:
            create_alert(
                cursor, user_id,
                'goal_achieved',
                f"🎯 Congratulations! You've achieved your {goal['goal_type']} goal of ${goal['goal_amount']}!",
                conn
            )
    except Exception as e:
        print(f"Goal alert error: {e}")

def create_alert(cursor, user_id, alert_type, message, conn):
    """Create a new alert"""
    try:
        # Check if similar alert already exists (don't spam)
        cursor.execute('''
            SELECT alert_id FROM user_alerts
            WHERE user_id = %s
            AND alert_type = %s
            AND message = %s
            AND created_at > NOW() - INTERVAL '1 hour'
        ''', [user_id, alert_type, message])
        
        existing = cursor.fetchone()
        
        if existing:
            return  # Don't create duplicate
        
        cursor.execute('''
            INSERT INTO user_alerts (user_id, alert_type, message)
            VALUES (%s, %s, %s)
            RETURNING alert_id
        ''', [user_id, alert_type, message])
        
        conn.commit()
    except Exception as e:
        print(f"Create alert error: {e}")
        
# =========================================================
# PARLAY ENDPOINTS
# =========================================================

@router.post("/parlays", response_model=ParlayResponse)
async def create_parlay(
    parlay: ParlayCreate,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Create a new parlay bet.
    
    Steps:
    1. Calculate combined odds
    2. Create parlay parent record
    3. Create individual leg bets (linked to parlay)
    4. Create transaction record
    5. Update account balance
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Validate
        if len(parlay.legs) < 2:
            raise HTTPException(400, "Parlay must have at least 2 legs")
        if len(parlay.legs) > 15:
            raise HTTPException(400, "Parlay cannot have more than 15 legs")
        
        # Calculate odds
        combined_odds = calculate_parlay_odds(parlay.legs)
        potential_payout = calculate_parlay_payout(parlay.stake_amount, combined_odds)
        sport_mix = get_sport_mix(parlay.legs)
        
        # Create parlay parent
        cursor.execute("""
            INSERT INTO parlays (
                user_id, account_id, total_legs, combined_odds_american,
                stake_amount, potential_payout, sport_mix, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING parlay_id
        """, [
            user_id,
            parlay.account_id,
            len(parlay.legs),
            combined_odds,
            parlay.stake_amount,
            potential_payout,
            sport_mix,
            parlay.notes
        ])
        
        parlay_id = cursor.fetchone()['parlay_id']
        
        # Create individual leg bets
        leg_ids = []
        for leg in parlay.legs:
            cursor.execute("""
                INSERT INTO bets (
                    user_id, account_id, parlay_id, bet_type, sport,
                    market_key, bet_side, line_value, odds_american,
                    stake_amount, game_id, player_id, sport_id, notes, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING bet_id
            """, [
                user_id,
                parlay.account_id,
                parlay_id,
                leg.bet_type,
                leg.sport,
                leg.market_key,
                leg.bet_side,
                leg.line_value,
                leg.odds_american,
                0,  # Legs don't have individual stakes
                leg.game_id,
                leg.player_id,
                leg.sport_id,
                leg.notes
            ])
            
            leg_ids.append(cursor.fetchone()['bet_id'])
        
        # Create transaction (deduct stake from account)
        cursor.execute("""
            INSERT INTO bankroll_transactions (
                account_id, user_id, transaction_type, amount, description
            )
            VALUES (%s, %s, 'bet_placed', %s, %s)
        """, [
            parlay.account_id,
            user_id,
            -parlay.stake_amount,
            f"Parlay bet placed: {len(parlay.legs)} legs, {sport_mix}"
        ])
        
        # Update account balance
        cursor.execute("""
            UPDATE bankroll_accounts
            SET current_balance = current_balance - %s,
                updated_at = NOW()
            WHERE account_id = %s
        """, [parlay.stake_amount, parlay.account_id])
        
        conn.commit()
        
        # Fetch created parlay with details
        cursor.execute("""
            SELECT * FROM v_parlay_details
            WHERE parlay_id = %s
        """, [parlay_id])
        
        result = cursor.fetchone()
        cursor.close()
        
        return result
        
    except Exception as e:
        if cursor:
            cursor.close()
        conn.rollback()
        print(f"❌ Create Parlay Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to create parlay: {str(e)}")


@router.get("/parlays", response_model=List[ParlayResponse])
async def get_parlays(
    user_id: int = Query(default=1),
    status: Optional[str] = Query(default=None),
    account_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, le=500),
    conn = Depends(get_db)
):
    """Get user's parlays with filtering"""
    cursor = None
    try:
        cursor = conn.cursor()
        
        where_clauses = ["user_id = %s"]
        params = [user_id]
        
        if status:
            where_clauses.append("parlay_status = %s")
            params.append(status)
        
        if account_id:
            where_clauses.append("account_id = %s")
            params.append(account_id)
        
        where_clause = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT * FROM v_parlay_details
            WHERE {where_clause}
            ORDER BY placed_at DESC
            LIMIT %s
        """, params + [limit])
        
        parlays = cursor.fetchall()
        cursor.close()
        
        return parlays
        
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(500, f"Failed to fetch parlays: {str(e)}")


@router.get("/parlays/{parlay_id}", response_model=ParlayResponse)
async def get_parlay(
    parlay_id: int,
    conn = Depends(get_db)
):
    """Get single parlay with all legs"""
    cursor = None
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM v_parlay_details
            WHERE parlay_id = %s
        """, [parlay_id])
        
        parlay = cursor.fetchone()
        cursor.close()
        
        if not parlay:
            raise HTTPException(404, "Parlay not found")
        
        return parlay
        
    except HTTPException:
        raise
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(500, f"Failed to fetch parlay: {str(e)}")


@router.post("/parlays/{parlay_id}/settle")
async def settle_parlay(
    parlay_id: int,
    leg_results: dict,  # {bet_id: 'won'/'lost'/'push'}
    conn = Depends(get_db)
):
    """
    Settle a parlay by settling all legs.
    
    Rules:
    - ALL legs must be 'won' for parlay to win
    - ANY leg 'lost' = parlay lost
    - If any leg is 'push', it's removed from parlay odds calculation
    
    Request Body:
    {
        "123": "won",
        "124": "won", 
        "125": "lost"
    }
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get parlay details
        cursor.execute("""
            SELECT p.*, ba.current_balance
            FROM parlays p
            JOIN bankroll_accounts ba ON p.account_id = ba.account_id
            WHERE p.parlay_id = %s
        """, [parlay_id])
        
        parlay = cursor.fetchone()
        if not parlay:
            raise HTTPException(404, "Parlay not found")
        
        if parlay['status'] != 'pending':
            raise HTTPException(400, "Parlay already settled")
        
        # Update individual leg statuses
        all_won = True
        any_lost = False
        push_count = 0
        
        for bet_id_str, result in leg_results.items():
            bet_id = int(bet_id_str)
            
            if result not in ['won', 'lost', 'push']:
                raise HTTPException(400, f"Invalid result for bet {bet_id}: {result}")
            
            cursor.execute("""
                UPDATE bets
                SET status = %s, settled_at = NOW(), updated_at = NOW()
                WHERE bet_id = %s AND parlay_id = %s
            """, [result, bet_id, parlay_id])
            
            if result == 'lost':
                any_lost = True
                all_won = False
            elif result == 'push':
                push_count += 1
            elif result != 'won':
                all_won = False
        
        # Determine parlay result
        if any_lost:
            parlay_status = 'lost'
            actual_payout = 0
            profit_loss = -parlay['stake_amount']
        elif all_won:
            parlay_status = 'won'
            # If there were pushes, recalculate odds without those legs
            if push_count > 0:
                # Get winning legs' odds
                cursor.execute("""
                    SELECT odds_american FROM bets
                    WHERE parlay_id = %s AND status = 'won'
                """, [parlay_id])
                
                winning_legs_odds = [row['odds_american'] for row in cursor.fetchall()]
                
                # Recalculate parlay odds
                from types import SimpleNamespace
                legs = [SimpleNamespace(odds_american=odds) for odds in winning_legs_odds]
                recalc_odds = calculate_parlay_odds(legs)
                actual_payout = calculate_parlay_payout(parlay['stake_amount'], recalc_odds)
            else:
                actual_payout = parlay['potential_payout']
            
            profit_loss = actual_payout - parlay['stake_amount']
        else:
            # Some legs still pending
            raise HTTPException(400, "Not all legs have been settled")
        
        # Update parlay
        cursor.execute("""
            UPDATE parlays
            SET status = %s,
                actual_payout = %s,
                profit_loss = %s,
                settled_at = NOW(),
                updated_at = NOW()
            WHERE parlay_id = %s
        """, [parlay_status, actual_payout, profit_loss, parlay_id])
        
        # Update account balance (if won)
        if parlay_status == 'won':
            cursor.execute("""
                UPDATE bankroll_accounts
                SET current_balance = current_balance + %s,
                    updated_at = NOW()
                WHERE account_id = %s
            """, [actual_payout, parlay['account_id']])
            
            # Create transaction
            cursor.execute("""
                INSERT INTO bankroll_transactions (
                    account_id, user_id, transaction_type, amount, description
                )
                VALUES (%s, %s, 'bet_settled', %s, %s)
            """, [
                parlay['account_id'],
                parlay['user_id'],
                actual_payout,
                f"Parlay won: {parlay['total_legs']} legs, +${profit_loss:.2f}"
            ])
        
        conn.commit()
        
        # TODO: Check for alerts (winning streak, profit milestone, etc.)
        
        # Return updated parlay
        cursor.execute("""
            SELECT * FROM v_parlay_details
            WHERE parlay_id = %s
        """, [parlay_id])
        
        result = cursor.fetchone()
        cursor.close()
        
        return result
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        if cursor:
            cursor.close()
        print(f"❌ Settle Parlay Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to settle parlay: {str(e)}")


@router.delete("/parlays/{parlay_id}")
async def delete_parlay(
    parlay_id: int,
    conn = Depends(get_db)
):
    """
    Delete a parlay (only if pending).
    Cascades to delete all leg bets.
    Refunds stake to account.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get parlay
        cursor.execute("""
            SELECT * FROM parlays WHERE parlay_id = %s
        """, [parlay_id])
        
        parlay = cursor.fetchone()
        if not parlay:
            raise HTTPException(404, "Parlay not found")
        
        if parlay['status'] != 'pending':
            raise HTTPException(400, "Can only delete pending parlays")
        
        # Refund stake
        cursor.execute("""
            UPDATE bankroll_accounts
            SET current_balance = current_balance + %s
            WHERE account_id = %s
        """, [parlay['stake_amount'], parlay['account_id']])
        
        # Create refund transaction
        cursor.execute("""
            INSERT INTO bankroll_transactions (
                account_id, user_id, transaction_type, amount, description
            )
            VALUES (%s, %s, 'adjustment', %s, %s)
        """, [
            parlay['account_id'],
            parlay['user_id'],
            parlay['stake_amount'],
            f"Parlay cancelled (refund)"
        ])
        
        # Delete parlay (cascades to bets via FK)
        cursor.execute("""
            DELETE FROM parlays WHERE parlay_id = %s
        """, [parlay_id])
        
        conn.commit()
        cursor.close()
        
        return {"message": "Parlay deleted successfully", "refunded": float(parlay['stake_amount'])}
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        if cursor:
            cursor.close()
        raise HTTPException(500, f"Failed to delete parlay: {str(e)}")
    
# =========================================================
# MULTI-SPORT ANALYTICS
# =========================================================

@router.get("/analytics/by-sport")
async def get_analytics_by_sport(
    user_id: int = Query(default=1),
    days: int = Query(default=30, le=365),
    conn = Depends(get_db)
):
    """
    Performance breakdown by sport.
    
    Returns stats for each sport user has bet on:
    - Total bets, win rate, ROI
    - Total staked, profit/loss
    - Best/worst performing sport
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                sport,
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE status = 'won') as won_bets,
                COUNT(*) FILTER (WHERE status = 'lost') as lost_bets,
                COUNT(*) FILTER (WHERE status = 'push') as push_bets,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_bets,
                
                COALESCE(SUM(stake_amount), 0) as total_staked,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END,
                1) as win_rate,
                
                ROUND(
                    CASE 
                        WHEN SUM(stake_amount) > 0 THEN
                            (SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')) / 
                             SUM(stake_amount) * 100)
                        ELSE 0
                    END,
                1) as roi_percentage,
                
                ROUND(AVG(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 2) as avg_profit_per_bet,
                MAX(profit_loss) as best_win,
                MIN(profit_loss) as worst_loss
                
            FROM bets
            WHERE user_id = %s
            AND placed_at >= NOW() - INTERVAL '%s days'
            AND parlay_id IS NULL  -- Exclude parlay legs
            GROUP BY sport
            ORDER BY profit_loss DESC
        """
        
        cursor.execute(query, [user_id, days])
        by_sport = cursor.fetchall()
        
        # Calculate totals
        total_bets = sum(s['total_bets'] for s in by_sport)
        total_profit = sum(s['profit_loss'] for s in by_sport)
        
        # Find best/worst
        best_sport = max(by_sport, key=lambda x: x['profit_loss']) if by_sport else None
        worst_sport = min(by_sport, key=lambda x: x['profit_loss']) if by_sport else None
        
        cursor.close()
        
        return {
            "by_sport": [
                {
                    "sport": row['sport'],
                    "total_bets": row['total_bets'],
                    "won_bets": row['won_bets'],
                    "lost_bets": row['lost_bets'],
                    "push_bets": row['push_bets'],
                    "pending_bets": row['pending_bets'],
                    "total_staked": float(row['total_staked']),
                    "profit_loss": float(row['profit_loss']),
                    "win_rate": float(row['win_rate']),
                    "roi_percentage": float(row['roi_percentage']),
                    "avg_profit_per_bet": float(row['avg_profit_per_bet']) if row['avg_profit_per_bet'] else 0,
                    "best_win": float(row['best_win']) if row['best_win'] else 0,
                    "worst_loss": float(row['worst_loss']) if row['worst_loss'] else 0
                }
                for row in by_sport
            ],
            "summary": {
                "total_bets": total_bets,
                "total_profit": float(total_profit),
                "best_sport": {
                    "sport": best_sport['sport'],
                    "profit_loss": float(best_sport['profit_loss'])
                } if best_sport else None,
                "worst_sport": {
                    "sport": worst_sport['sport'],
                    "profit_loss": float(worst_sport['profit_loss'])
                } if worst_sport else None
            }
        }
        
    except Exception as e:
        if cursor:
            cursor.close()
        print(f"❌ By Sport Analytics Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to get sport analytics: {str(e)}")


@router.get("/analytics/parlay-stats")
async def get_parlay_stats(
    user_id: int = Query(default=1),
    days: int = Query(default=30, le=365),
    conn = Depends(get_db)
):
    """
    Parlay-specific analytics.
    
    Returns:
    - Overall parlay performance
    - Win rate by leg count (2-leg, 3-leg, etc.)
    - Single sport vs multi-sport performance
    - Average odds and payouts
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Overall parlay stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_parlays,
                COUNT(*) FILTER (WHERE status = 'won') as won_parlays,
                COUNT(*) FILTER (WHERE status = 'lost') as lost_parlays,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_parlays,
                
                COALESCE(SUM(stake_amount), 0) as total_staked,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost')), 0) as profit_loss,
                
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END,
                1) as win_rate,
                
                ROUND(AVG(combined_odds_american), 0) as avg_odds,
                ROUND(AVG(total_legs), 1) as avg_legs,
                ROUND(AVG(potential_payout), 2) as avg_potential_payout
                
            FROM parlays
            WHERE user_id = %s
            AND placed_at >= NOW() - INTERVAL '%s days'
        """, [user_id, days])
        
        overall = cursor.fetchone()
        
        # By leg count
        cursor.execute("""
            SELECT 
                total_legs,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE status = 'won') as won,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END,
                1) as win_rate,
                COALESCE(SUM(profit_loss), 0) as profit_loss
            FROM parlays
            WHERE user_id = %s
            AND placed_at >= NOW() - INTERVAL '%s days'
            GROUP BY total_legs
            ORDER BY total_legs
        """, [user_id, days])
        
        by_leg_count = cursor.fetchall()
        
        # Single sport vs multi-sport
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN sport_mix LIKE '%+%' THEN 'Multi-Sport'
                    ELSE 'Single Sport'
                END as parlay_type,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE status = 'won') as won,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END,
                1) as win_rate,
                COALESCE(SUM(profit_loss), 0) as profit_loss
            FROM parlays
            WHERE user_id = %s
            AND placed_at >= NOW() - INTERVAL '%s days'
            GROUP BY parlay_type
        """, [user_id, days])
        
        by_type = cursor.fetchall()
        
        cursor.close()
        
        return {
            "overall": {
                "total_parlays": overall['total_parlays'],
                "won_parlays": overall['won_parlays'],
                "lost_parlays": overall['lost_parlays'],
                "pending_parlays": overall['pending_parlays'],
                "total_staked": float(overall['total_staked']),
                "profit_loss": float(overall['profit_loss']),
                "win_rate": float(overall['win_rate']),
                "avg_odds": int(overall['avg_odds']) if overall['avg_odds'] else 0,
                "avg_legs": float(overall['avg_legs']) if overall['avg_legs'] else 0,
                "avg_potential_payout": float(overall['avg_potential_payout']) if overall['avg_potential_payout'] else 0
            },
            "by_leg_count": [
                {
                    "legs": row['total_legs'],
                    "count": row['count'],
                    "won": row['won'],
                    "win_rate": float(row['win_rate']),
                    "profit_loss": float(row['profit_loss'])
                }
                for row in by_leg_count
            ],
            "by_type": [
                {
                    "type": row['parlay_type'],
                    "count": row['count'],
                    "won": row['won'],
                    "win_rate": float(row['win_rate']),
                    "profit_loss": float(row['profit_loss'])
                }
                for row in by_type
            ]
        }
        
    except Exception as e:
        if cursor:
            cursor.close()
        print(f"❌ Parlay Stats Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to get parlay stats: {str(e)}")


@router.get("/analytics/sport-trends")
async def get_sport_trends(
    user_id: int = Query(default=1),
    sport: str = Query(default=None),
    days: int = Query(default=90, le=365),
    conn = Depends(get_db)
):
    """
    Daily profit/loss trends by sport.
    
    Used for sport-specific trend charts.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        where_clauses = ["user_id = %s", "parlay_id IS NULL"]
        params = [user_id]
        
        if sport:
            where_clauses.append("sport = %s")
            params.append(sport)
        
        where_clause = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT 
                DATE(placed_at) as date,
                sport,
                COUNT(*) as bets_count,
                COALESCE(SUM(profit_loss) FILTER (WHERE status IN ('won', 'lost', 'push')), 0) as profit_loss,
                COUNT(*) FILTER (WHERE status = 'won') as won_count
            FROM bets
            WHERE {where_clause}
            AND placed_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(placed_at), sport
            ORDER BY date DESC, sport
        """, params + [days])
        
        trends = cursor.fetchall()
        cursor.close()
        
        return [
            {
                "date": str(row['date']),
                "sport": row['sport'],
                "bets_count": row['bets_count'],
                "profit_loss": float(row['profit_loss']),
                "won_count": row['won_count']
            }
            for row in trends
        ]
        
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(500, f"Failed to get sport trends: {str(e)}")

