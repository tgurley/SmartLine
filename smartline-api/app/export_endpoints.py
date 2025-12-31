"""
Export & Reporting Endpoints - Phase 4B
========================================
Add these to your bankroll_endpoints.py or create as separate router
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List, Literal
from datetime import datetime, date
from decimal import Decimal
import csv
import io
import tempfile
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db():
    """Database connection dependency."""
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

# Will add openpyxl and reportlab imports when we get to Excel/PDF

router = APIRouter(prefix="/bankroll/export", tags=["Export & Reports"])

# =========================================================
# CSV EXPORT
# =========================================================

@router.get("/csv")
async def export_csv(
    user_id: int = Query(default=1),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    bookmaker: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    conn = Depends(get_db)
):
    """
    Export bets to CSV format with optional filtering.
    
    **Use Case:** Download betting data for analysis
    **Returns:** CSV file download
    """
    cursor = conn.cursor()
    
    try:
        # Build dynamic WHERE clause
        where_clauses = ["b.user_id = %s"]
        params = [user_id]
        
        if start_date:
            where_clauses.append("DATE(b.placed_at) >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("DATE(b.placed_at) <= %s")
            params.append(end_date)
        
        if bookmaker:
            where_clauses.append("ba.bookmaker_name = %s")
            params.append(bookmaker)
        
        if market:
            where_clauses.append("b.market_key = %s")
            params.append(market)
        
        if status:
            where_clauses.append("b.status = %s")
            params.append(status)
        
        if search:
            where_clauses.append("(b.notes ILIKE %s OR b.bet_side ILIKE %s)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        where_clause = " AND ".join(where_clauses)
        
        # Fetch bets with all details
        query = f"""
            SELECT 
                b.bet_id,
                TO_CHAR(b.placed_at, 'YYYY-MM-DD HH24:MI:SS') as placed_at,
                ba.bookmaker_name,
                b.bet_type,
                b.sport,
                b.market_key,
                b.bet_side,
                b.line_value,
                b.odds_american,
                b.odds_decimal,
                b.stake_amount,
                b.potential_payout,
                b.status,
                b.actual_payout,
                b.profit_loss,
                TO_CHAR(b.settled_at, 'YYYY-MM-DD HH24:MI:SS') as settled_at,
                b.notes
            FROM bets b
            LEFT JOIN bankroll_accounts ba ON b.account_id = ba.account_id
            WHERE {where_clause}
            ORDER BY b.placed_at DESC
        """
        
        cursor.execute(query, params)
        bets = cursor.fetchall()
        cursor.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Bet ID', 'Date Placed', 'Bookmaker', 'Bet Type', 'Sport', 
            'Market', 'Side', 'Line', 'Odds (American)', 'Odds (Decimal)',
            'Stake', 'Potential Payout', 'Status', 'Actual Payout', 
            'Profit/Loss', 'Settled Date', 'Notes'
        ])
        
        # Write data
        for bet in bets:
            writer.writerow([
                bet['bet_id'],
                bet['placed_at'],
                bet['bookmaker_name'] or 'N/A',
                bet['bet_type'],
                bet['sport'],
                bet['market_key'],
                bet['bet_side'],
                bet['line_value'] or '',
                bet['odds_american'] or '',
                bet['odds_decimal'] or '',
                float(bet['stake_amount']) if bet['stake_amount'] else '',
                float(bet['potential_payout']) if bet['potential_payout'] else '',
                bet['status'],
                float(bet['actual_payout']) if bet['actual_payout'] else '',
                float(bet['profit_loss']) if bet['profit_loss'] else '',
                bet['settled_at'] or '',
                bet['notes'] or ''
            ])
        
        # Prepare response
        output.seek(0)
        
        # Generate filename
        filename = f"bets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")

# =========================================================
# SUMMARY REPORT (JSON for preview)
# =========================================================

@router.get("/summary")
async def get_export_summary(
    user_id: int = Query(default=1),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    bookmaker: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    conn = Depends(get_db)
):
    """
    Get summary statistics for export preview.
    
    **Use Case:** Show user what they're about to export
    **Returns:** Summary stats
    """
    cursor = conn.cursor()
    
    try:
        # Build WHERE clause (same as CSV export)
        where_clauses = ["b.user_id = %s"]
        params = [user_id]
        
        if start_date:
            where_clauses.append("DATE(b.placed_at) >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("DATE(b.placed_at) <= %s")
            params.append(end_date)
        
        if bookmaker:
            where_clauses.append("ba.bookmaker_name = %s")
            params.append(bookmaker)
        
        if market:
            where_clauses.append("b.market_key = %s")
            params.append(market)
        
        if status:
            where_clauses.append("b.status = %s")
            params.append(status)
        
        where_clause = " AND ".join(where_clauses)
        
        # Get summary stats
        query = f"""
            SELECT 
                COUNT(*) as total_bets,
                COUNT(*) FILTER (WHERE b.status = 'won') as won_bets,
                COUNT(*) FILTER (WHERE b.status = 'lost') as lost_bets,
                COUNT(*) FILTER (WHERE b.status = 'push') as push_bets,
                COUNT(*) FILTER (WHERE b.status = 'pending') as pending_bets,
                COALESCE(SUM(b.stake_amount), 0) as total_staked,
                COALESCE(SUM(b.profit_loss) FILTER (WHERE b.status IN ('won', 'lost', 'push')), 0) as total_profit_loss,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE b.status IN ('won', 'lost')) > 0 THEN
                            (COUNT(*) FILTER (WHERE b.status = 'won')::numeric / 
                             COUNT(*) FILTER (WHERE b.status IN ('won', 'lost')) * 100)
                        ELSE 0
                    END,
                1) as win_rate,
                MIN(DATE(b.placed_at)) as earliest_bet,
                MAX(DATE(b.placed_at)) as latest_bet
            FROM bets b
            LEFT JOIN bankroll_accounts ba ON b.account_id = ba.account_id
            WHERE {where_clause}
        """
        
        cursor.execute(query, params)
        summary = cursor.fetchone()
        cursor.close()
        
        return {
            "total_bets": summary['total_bets'],
            "won_bets": summary['won_bets'],
            "lost_bets": summary['lost_bets'],
            "push_bets": summary['push_bets'],
            "pending_bets": summary['pending_bets'],
            "total_staked": float(summary['total_staked']),
            "total_profit_loss": float(summary['total_profit_loss']),
            "win_rate": float(summary['win_rate']),
            "earliest_bet": str(summary['earliest_bet']) if summary['earliest_bet'] else None,
            "latest_bet": str(summary['latest_bet']) if summary['latest_bet'] else None,
            "date_range_days": (summary['latest_bet'] - summary['earliest_bet']).days if summary['earliest_bet'] and summary['latest_bet'] else 0
        }
        
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

# =========================================================
# FILTER OPTIONS (Get available bookmakers/markets)
# =========================================================

@router.get("/filter-options")
async def get_filter_options(
    user_id: int = Query(default=1),
    conn = Depends(get_db)
):
    """
    Get available filter options (bookmakers, markets, etc).
    
    **Use Case:** Populate filter dropdowns
    **Returns:** Lists of available filter values
    """
    cursor = conn.cursor()
    
    try:
        # Get unique bookmakers
        cursor.execute("""
            SELECT DISTINCT ba.bookmaker_name
            FROM bankroll_accounts ba
            WHERE ba.user_id = %s
            ORDER BY ba.bookmaker_name
        """, [user_id])
        bookmakers = [row['bookmaker_name'] for row in cursor.fetchall()]
        
        # Get unique markets
        cursor.execute("""
            SELECT DISTINCT market_key
            FROM bets
            WHERE user_id = %s
            AND market_key IS NOT NULL
            ORDER BY market_key
        """, [user_id])
        markets = [row['market_key'] for row in cursor.fetchall()]
        
        # Get unique sports
        cursor.execute("""
            SELECT DISTINCT sport
            FROM bets
            WHERE user_id = %s
            AND sport IS NOT NULL
            ORDER BY sport
        """, [user_id])
        sports = [row['sport'] for row in cursor.fetchall()]
        
        cursor.close()
        
        return {
            "bookmakers": bookmakers,
            "markets": markets,
            "sports": sports,
            "statuses": ["pending", "won", "lost", "push", "cancelled"]
        }
        
    except Exception as e:
        if cursor:
            cursor.close()
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")