function BacktestResults({ response }) {
  return (
    <section>
      <h2>Results</h2>

      <div>
        <p><b>Bets:</b> {response.bets}</p>
        <p><b>Win %:</b> {response.win_pct}%</p>
        <p><b>ROI:</b> {response.roi_pct}%</p>
      </div>

      <table>
        <thead>
          <tr>
            <th>Game</th>
            <th>Side</th>
            <th>Spread</th>
            <th>Result</th>
            <th>Profit</th>
          </tr>
        </thead>
        <tbody>
          {response.results.map((r, i) => (
            <tr key={i}>
              <td>{r.home_team} vs {r.away_team}</td>
              <td>{r.side}</td>
              <td>{r.spread}</td>
              <td>{r.bet_result}</td>
              <td>{r.profit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default BacktestResults;
