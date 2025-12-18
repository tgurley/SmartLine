from fastapi import FastAPI
from app.models import StrategyRequest
from app.crud import backtest_strategy
from app.database import get_connection

app = FastAPI(title="SmartLine NFL Betting Intelligence")

@app.post("/backtest")
def backtest(strategy: StrategyRequest):
    rows = backtest_strategy(strategy)

    bets = len(rows)
    wins = sum(1 for r in rows if r["profit"] > 0)
    total_profit = sum(r["profit"] for r in rows)

    roi = (total_profit / (bets * strategy.stake) * 100) if bets > 0 else 0

    return {
        "strategy": strategy.name,
        "bets": bets,
        "wins": wins,
        "win_pct": round((wins / bets) * 100, 2) if bets else 0,
        "total_profit": round(total_profit, 2),
        "roi_pct": round(roi, 2),
        "results": rows
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    conn = get_connection()
    conn.close()
    return {"db": "ok"}

@app.get("/db/verify")
def db_verify():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
