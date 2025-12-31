"""
Bankroll Manager - Settings Endpoints
======================================
User settings and preferences for bankroll management.

Endpoints:
1. GET    /bankroll/settings - Get user settings
2. PUT    /bankroll/settings - Update settings
3. POST   /bankroll/settings/reset - Reset to defaults
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

# This can be added to bankroll_endpoints.py or kept separate
# For now, showing as separate for clarity

# =========================================================
# RESPONSE MODELS
# =========================================================

class BankrollSettings(BaseModel):
    settings_id: Optional[int] = None
    user_id: int
    
    # Betting Limits
    daily_limit: Optional[Decimal] = Field(None, description="Maximum bet amount per day")
    weekly_limit: Optional[Decimal] = Field(None, description="Maximum bet amount per week")
    monthly_limit: Optional[Decimal] = Field(None, description="Maximum bet amount per month")
    
    # Unit Settings
    unit_size_type: str = Field(default="fixed", description="'fixed' or 'percentage'")
    unit_size_value: Decimal = Field(default=100, description="Dollar amount or percentage")
    
    # Risk Settings
    max_bet_percentage: Decimal = Field(default=5, description="Max bet as % of bankroll")
    enable_stop_loss: bool = Field(default=False)
    stop_loss_amount: Optional[Decimal] = None
    
    # Notifications
    enable_limit_alerts: bool = Field(default=True)
    enable_streak_alerts: bool = Field(default=True)
    alert_threshold_percentage: Decimal = Field(default=80, description="Alert when reaching X% of limit")
    
    # Goals
    daily_profit_goal: Optional[Decimal] = None
    weekly_profit_goal: Optional[Decimal] = None
    monthly_profit_goal: Optional[Decimal] = None
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SettingsUpdate(BaseModel):
    daily_limit: Optional[Decimal] = None
    weekly_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    unit_size_type: Optional[str] = None
    unit_size_value: Optional[Decimal] = None
    max_bet_percentage: Optional[Decimal] = None
    enable_stop_loss: Optional[bool] = None
    stop_loss_amount: Optional[Decimal] = None
    enable_limit_alerts: Optional[bool] = None
    enable_streak_alerts: Optional[bool] = None
    alert_threshold_percentage: Optional[Decimal] = None
    daily_profit_goal: Optional[Decimal] = None
    weekly_profit_goal: Optional[Decimal] = None
    monthly_profit_goal: Optional[Decimal] = None

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
# SETTINGS ENDPOINTS
# =========================================================

# Note: Add these to your existing bankroll router
router = APIRouter(prefix="/bankroll", tags=["Bankroll Manager"])

def get_user_settings(user_id: int, conn):
    """Helper function to get settings."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bankroll_settings WHERE user_id = %s
    """, [user_id])
    settings = cursor.fetchone()
    cursor.close()
    return settings

def create_default_settings(user_id: int, conn):
    """Helper function to create default settings."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bankroll_settings (user_id)
        VALUES (%s)
        RETURNING *
    """, [user_id])
    settings = cursor.fetchone()
    conn.commit()
    cursor.close()
    return settings

# Add this to your router:
@router.get("/settings")
async def get_settings(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Get user bankroll settings.
    
    **Use Case:** Settings page, limit checks
    **Returns:** User settings or defaults
    '''
    settings = get_user_settings(user_id, conn)
    
    if not settings:
        # Create default settings
        settings = create_default_settings(user_id, conn)
    
    # Convert datetime objects to strings
    if settings:
        settings = dict(settings)
        if settings.get('created_at'):
            settings['created_at'] = settings['created_at'].isoformat()
        if settings.get('updated_at'):
            settings['updated_at'] = settings['updated_at'].isoformat()
    
    return settings

@router.put("/settings")
async def update_settings(
    settings_update: SettingsUpdate,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Update user settings.
    
    **Use Case:** Save settings from settings page
    **Returns:** Updated settings
    '''
    cursor = conn.cursor()
    
    try:
        # Check if settings exist
        existing = get_user_settings(user_id, conn)
        
        if not existing:
            # Create first
            existing = create_default_settings(user_id, conn)
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        for field, value in settings_update.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)
        
        if not update_fields:
            result = dict(existing)
            if result.get('created_at'):
                result['created_at'] = result['created_at'].isoformat()
            if result.get('updated_at'):
                result['updated_at'] = result['updated_at'].isoformat()
            return result
        
        params.append(user_id)
        query = f'''
            UPDATE bankroll_settings
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE user_id = %s
            RETURNING *
        '''
        
        cursor.execute(query, params)
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        # Convert datetime to string
        result = dict(updated)
        if result.get('created_at'):
            result['created_at'] = result['created_at'].isoformat()
        if result.get('updated_at'):
            result['updated_at'] = result['updated_at'].isoformat()
        
        return result
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.post("/settings/reset")
async def reset_settings(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Reset settings to defaults.
    
    **Use Case:** Reset button on settings page
    **Returns:** Default settings
    '''
    cursor = conn.cursor()
    
    try:
        # Delete existing
        cursor.execute("DELETE FROM bankroll_settings WHERE user_id = %s", [user_id])
        conn.commit()
        
        # Create new defaults
        settings = create_default_settings(user_id, conn)
        
        # Convert datetime to string
        result = dict(settings)
        if result.get('created_at'):
            result['created_at'] = result['created_at'].isoformat()
        if result.get('updated_at'):
            result['updated_at'] = result['updated_at'].isoformat()
        
        return result
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")
"""

# =========================================================
# HELPER ENDPOINTS FOR LIMITS CHECKING
# =========================================================

"""
@router.get("/settings/check-limits")
async def check_betting_limits(
    stake_amount: Decimal,
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Check if a bet amount would exceed any limits.
    
    **Use Case:** Validate before placing bet
    **Returns:** Warnings if limits would be exceeded
    '''
    cursor = conn.cursor()
    
    # Get settings
    settings = get_user_settings(user_id, conn)
    if not settings:
        return {"allowed": True, "warnings": []}
    
    warnings = []
    
    # Check daily limit
    if settings['daily_limit']:
        cursor.execute('''
            SELECT COALESCE(SUM(stake_amount), 0) as daily_total
            FROM bets
            WHERE user_id = %s
            AND DATE(placed_at) = CURRENT_DATE
        ''', [user_id])
        daily_total = cursor.fetchone()['daily_total']
        
        if daily_total + stake_amount > settings['daily_limit']:
            warnings.append({
                "type": "daily_limit",
                "message": f"Would exceed daily limit of {settings['daily_limit']}",
                "current": float(daily_total),
                "limit": float(settings['daily_limit'])
            })
    
    # Check weekly limit
    if settings['weekly_limit']:
        cursor.execute('''
            SELECT COALESCE(SUM(stake_amount), 0) as weekly_total
            FROM bets
            WHERE user_id = %s
            AND placed_at >= date_trunc('week', CURRENT_DATE)
        ''', [user_id])
        weekly_total = cursor.fetchone()['weekly_total']
        
        if weekly_total + stake_amount > settings['weekly_limit']:
            warnings.append({
                "type": "weekly_limit",
                "message": f"Would exceed weekly limit of {settings['weekly_limit']}",
                "current": float(weekly_total),
                "limit": float(settings['weekly_limit'])
            })
    
    # Check monthly limit
    if settings['monthly_limit']:
        cursor.execute('''
            SELECT COALESCE(SUM(stake_amount), 0) as monthly_total
            FROM bets
            WHERE user_id = %s
            AND placed_at >= date_trunc('month', CURRENT_DATE)
        ''', [user_id])
        monthly_total = cursor.fetchone()['monthly_total']
        
        if monthly_total + stake_amount > settings['monthly_limit']:
            warnings.append({
                "type": "monthly_limit",
                "message": f"Would exceed monthly limit of {settings['monthly_limit']}",
                "current": float(monthly_total),
                "limit": float(settings['monthly_limit'])
            })
    
    # Check max bet percentage
    if settings['max_bet_percentage']:
        cursor.execute('''
            SELECT COALESCE(SUM(current_balance), 0) as total_bankroll
            FROM bankroll_accounts
            WHERE user_id = %s
        ''', [user_id])
        bankroll = cursor.fetchone()['total_bankroll']
        max_bet = bankroll * (settings['max_bet_percentage'] / 100)
        
        if stake_amount > max_bet:
            warnings.append({
                "type": "max_percentage",
                "message": f"Exceeds {settings['max_bet_percentage']}% of bankroll",
                "max_recommended": float(max_bet),
                "bankroll": float(bankroll)
            })
    
    cursor.close()
    
    return {
        "allowed": len(warnings) == 0,
        "warnings": warnings
    }

@router.get("/settings/recommended-unit")
async def get_recommended_unit(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    '''
    Calculate recommended unit size based on settings.
    
    **Use Case:** Unit calculator on settings page
    **Returns:** Recommended bet unit
    '''
    cursor = conn.cursor()
    
    # Get current bankroll
    cursor.execute('''
        SELECT COALESCE(SUM(current_balance), 0) as total_bankroll
        FROM bankroll_accounts
        WHERE user_id = %s
    ''', [user_id])
    bankroll = cursor.fetchone()['total_bankroll']
    
    # Get settings
    settings = get_user_settings(user_id, conn)
    cursor.close()
    
    if not settings:
        # Default: 1% of bankroll
        return {
            "unit_size": float(bankroll * Decimal('0.01')),
            "bankroll": float(bankroll),
            "percentage": 1.0
        }
    
    if settings['unit_size_type'] == 'fixed':
        return {
            "unit_size": float(settings['unit_size_value']),
            "bankroll": float(bankroll),
            "percentage": float((settings['unit_size_value'] / bankroll * 100) if bankroll > 0 else 0)
        }
    else:  # percentage
        unit = bankroll * (settings['unit_size_value'] / 100)
        return {
            "unit_size": float(unit),
            "bankroll": float(bankroll),
            "percentage": float(settings['unit_size_value'])
        }

