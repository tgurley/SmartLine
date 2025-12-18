from app.database import get_connection

def backtest_strategy(strategy):
    filters = strategy.filters
    stake = strategy.stake

    conditions = []
    params = []

    if filters.side:
        conditions.append("side = %s")
        params.append(filters.side)

    if filters.spread_min is not None:
        conditions.append("spread >= %s")
        params.append(filters.spread_min)

    if filters.spread_max is not None:
        conditions.append("spread <= %s")
        params.append(filters.spread_max)

    if filters.movement_signal:
        conditions.append("movement_signal = %s")
        params.append(filters.movement_signal)

    if filters.injury_diff_min is not None:
        conditions.append("injury_diff >= %s")
        params.append(filters.injury_diff_min)

    if filters.injury_diff_max is not None:
        conditions.append("injury_diff <= %s")
        params.append(filters.injury_diff_max)

    if filters.book:
        conditions.append("book = %s")
        params.append(filters.book)

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT *,
        CASE
            WHEN bet_result = 'win' AND price_american < 0
                THEN %s * (100.0 / ABS(price_american))
            WHEN bet_result = 'win' AND price_american > 0
                THEN %s * (price_american / 100.0)
            WHEN bet_result = 'loss'
                THEN -%s
            ELSE 0
        END AS profit
        FROM v_ats_spread_enriched
        {where_clause}
    """

    params = [stake, stake, stake] + params

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows
