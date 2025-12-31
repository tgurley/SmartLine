"""
Alert System Endpoints - Phase 4A Part 2
=========================================
Add these to your bankroll_endpoints.py
"""

# Add these Pydantic models

class Alert(BaseModel):
    alert_id: int
    user_id: int
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime

# Add these endpoints

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
# ALERT GENERATION FUNCTIONS
# =========================================================
# Call these from your settle_bet endpoint

def check_and_create_alerts(cursor, user_id, bet_id, conn):
    """
    Check for conditions that should trigger alerts and create them.
    Call this function after settling a bet.
    """
    
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

def check_streak_alerts(cursor, user_id, settings, conn):
    """Check for winning/losing streaks"""
    
    if not settings['enable_streak_alerts']:
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
    if streak['status'] == 'lost' and streak['streak_length'] >= 3:
        create_alert(
            cursor, user_id,
            'losing_streak',
            f"⚠️ You're on a {streak['streak_length']}-bet losing streak. Consider taking a break.",
            conn
        )
    
    # Alert on 5+ winning streak
    elif streak['status'] == 'won' and streak['streak_length'] >= 5:
        create_alert(
            cursor, user_id,
            'winning_streak',
            f"🔥 Amazing! You're on a {streak['streak_length']}-bet winning streak!",
            conn
        )

def check_limit_alerts(cursor, user_id, settings, conn):
    """Check if approaching betting limits"""
    
    if not settings['enable_limit_alerts']:
        return
    
    threshold = settings['alert_threshold_percentage'] / 100
    
    # Check daily limit
    cursor.execute('''
        SELECT COALESCE(SUM(stake_amount), 0) as daily_total
        FROM bets
        WHERE user_id = %s
        AND DATE(placed_at) = CURRENT_DATE
    ''', [user_id])
    
    result = cursor.fetchone()
    daily_total = float(result['daily_total'])
    daily_limit = float(settings['daily_limit'])
    
    if daily_total >= (daily_limit * threshold):
        percentage = (daily_total / daily_limit) * 100
        create_alert(
            cursor, user_id,
            'limit_warning',
            f"⚠️ You've used {percentage:.0f}% of your daily betting limit (${daily_total:.2f} / ${daily_limit:.2f})",
            conn
        )

def check_goal_alerts(cursor, user_id, conn):
    """Check for goal achievements"""
    
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

def create_alert(cursor, user_id, alert_type, message, conn):
    """Create a new alert"""
    
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


# =========================================================
# UPDATE YOUR SETTLE_BET ENDPOINT
# =========================================================

# In your existing settle_bet endpoint, add this at the end:

@router.post("/bets/{bet_id}/settle")
async def settle_bet(
    bet_id: int,
    status: Literal['won', 'lost', 'push'],
    actual_payout: Optional[Decimal] = None,
    conn = Depends(get_db)
):
    # ... existing settle logic ...
    
    # NEW: Check and create alerts
    check_and_create_alerts(cursor, user_id, bet_id, conn)
    
    # ... rest of function ...
