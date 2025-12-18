import { useState } from "react";

function App() {
  const [response, setResponse] = useState(null);

  const runBacktest = async () => {
    const payload = {
      name: "Home Steam Strategy",
      filters: {
        side: "home",
        spread_min: -7,
        spread_max: -1,
        movement_signal: "steam",
        injury_diff_max: -1
      },
      stake: 100
    };

    const res = await fetch("http://localhost:8000/backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    setResponse(data);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>SmartLine — NFL Betting Intelligence</h1>
      <button onClick={runBacktest}>Run Backtest</button>

      {response && (
        <>
          <h2>Results</h2>
          <p><b>Bets:</b> {response.bets}</p>
          <p><b>Win %:</b> {response.win_pct}%</p>
          <p><b>ROI:</b> {response.roi_pct}%</p>

          <table border="1" cellPadding="6">
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
        </>
      )}
    </div>
  );
}

export default App;
