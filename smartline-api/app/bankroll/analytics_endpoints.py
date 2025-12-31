"""
Advanced Analytics Endpoints - Phase 3
=======================================
Detailed performance analysis and insights
"""

# Add these endpoints to your bankroll_endpoints.py file
# Or include as a separate router

"""
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
"""
