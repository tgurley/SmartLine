import { useSearchParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchGames } from "../api/games";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  BarChart,
  Bar,
  Legend
} from "recharts";

function WeatherTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;

  const g = payload[0].payload;

  return (
    <div
      style={{
        background: "white",
        border: "1px solid #ccc",
        padding: "0.75rem",
        fontSize: "0.85rem"
      }}
    >
      <strong>{g.label}</strong>

      <div>🏈 Total Points: {g.totalPoints}</div>
      <div>⚠ Severity: {g.severity}</div>

      {g.isDome ? (
        <div>🏟 Dome game</div>
      ) : (
        <>
          <div>🌡 Temp: {g.tempF ?? "N/A"} °F</div>
          <div>💨 Wind: {g.windMph ?? "N/A"} mph</div>
          <div>
            🌧 Rain:{" "}
            {g.rainMm == null
              ? "N/A"
              : g.rainMm === 0
              ? "None"
              : `${g.rainMm} mm`}
          </div>
        </>
      )}
    </div>
  );
}


function Analytics() {
  const [searchParams, setSearchParams] = useSearchParams();


  const season = Number(searchParams.get("season")) || 2023;
  const week = Number(searchParams.get("week")) || 1;

  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [comparison, setComparison] = useState([]);

  const totals = games
    .filter(g => g.result)
    .map(g => ({
        gameId: g.game_id,
        totalPoints: g.result.home_score + g.result.away_score,
        severity: g.weather.severity_score,
        isDome: g.venue?.is_dome,
        tempF: g.weather.temp_f,
        windMph: g.weather.wind_mph,
        rainMm: g.weather.precip_mm,
        label: `${g.away_team.abbrev} @ ${g.home_team.abbrev}`
    }));


  const domeGames = totals.filter(g => g.isDome);
  const outdoorGames = totals.filter(g => !g.isDome);

  const buckets = {
    clear: { label: "Clear (0)", count: 0, totalPoints: 0 },
    moderate: { label: "Moderate (1–2)", count: 0, totalPoints: 0 },
    severe: { label: "Severe (3+)", count: 0, totalPoints: 0 }
    };

    outdoorGames.forEach(g => {
    if (g.severity === 0) {
        buckets.clear.count += 1;
        buckets.clear.totalPoints += g.totalPoints;
    } else if (g.severity <= 2) {
        buckets.moderate.count += 1;
        buckets.moderate.totalPoints += g.totalPoints;
    } else {
        buckets.severe.count += 1;
        buckets.severe.totalPoints += g.totalPoints;
    }
    });

    const bucketStats = Object.values(buckets)
    .filter(b => b.count > 0)
    .map(b => ({
        ...b,
        avgPoints: b.totalPoints / b.count
    }));


  function linearRegression(points) {
    if (points.length < 2) return null;

    const n = points.length;

    const sumX = points.reduce((s, p) => s + p.severity, 0);
    const sumY = points.reduce((s, p) => s + p.totalPoints, 0);
    const sumXY = points.reduce((s, p) => s + p.severity * p.totalPoints, 0);
    const sumXX = points.reduce((s, p) => s + p.severity * p.severity, 0);

    const slope =
        (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return { slope, intercept };
    }
  
  let trendlineData = [];
    let regression = null;

    if (outdoorGames.length >= 2) {
    regression = linearRegression(outdoorGames);

    const severities = outdoorGames.map(g => g.severity);
    const minSeverity = Math.min(...severities);
    const maxSeverity = Math.max(...severities);

    trendlineData = [
        {
        severity: minSeverity,
        totalPoints: regression.slope * minSeverity + regression.intercept
        },
        {
        severity: maxSeverity,
        totalPoints: regression.slope * maxSeverity + regression.intercept
        }
    ];
    }




  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await fetchGames(season, week);
      setGames(data.games);
      setLoading(false);
    }

    load();
  }, [season, week]);

  useEffect(() => {
    async function loadComparison() {
        const weeks = Array.from({ length: week }, (_, i) => i + 1);

        const responses = await Promise.all(
        weeks.map(w => fetchGames(season, w))
        );

        const weeklyStats = responses.map((res, i) => {
        const games = res.games.filter(g => g.result);

        const totals = games.map(
            g => g.result.home_score + g.result.away_score
        );

        const avgPoints =
            totals.length > 0
            ? totals.reduce((a, b) => a + b, 0) / totals.length
            : null;

        const outdoorGames = games.filter(g => !g.venue?.is_dome);
        const avgSeverity =
            outdoorGames.length > 0
            ? outdoorGames.reduce(
                (s, g) => s + g.weather.severity_score,
                0
                ) / outdoorGames.length
            : null;

        return {
            week: i + 1,
            avgPoints,
            avgSeverity,
            games: games.length
        };
        });

        setComparison(weeklyStats);
    }

    loadComparison();
    }, [season, week]);


  if (loading) return <p>Loading analytics...</p>;

  // Update URL when week changes
  const handleWeekChange = (newWeek) => {
    setSearchParams({ season, week: newWeek });
  };



  return (
    <section>
      <Link to={`/games?season=${season}&week=${week}`}>← Back to Games</Link>

      <h2>Analytics — Week {week} ({season})</h2>

      <p>
        Visual breakdown of scoring and weather impact for the selected week.
      </p>

      {/* Week Selector */}
      <label>
        Week:&nbsp;
        <select
          value={week}
          onChange={(e) => handleWeekChange(Number(e.target.value))}
        >
          {Array.from({ length: 18 }, (_, i) => i + 1).map((w) => (
            <option key={w} value={w}>
              {w}
            </option>
          ))}
        </select>
      </label>


      <h3>Total Points per Game</h3>

        <table>
        <thead>
            <tr>
            <th>Game</th>
            <th>Total Points</th>
            <th>Weather Severity</th>
            </tr>
        </thead>
        <tbody>
            {totals.map(t => (
            <tr key={t.gameId}>
                <td>{t.label}</td>
                <td>{t.totalPoints}</td>
                <td>{t.severity}</td>
            </tr>
            ))}
        </tbody>
        </table>


      <h3>Weather Severity vs Total Points</h3>

        <div style={{ width: "100%", height: 400 }}>
        <ResponsiveContainer>
            <ScatterChart
            margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
            <CartesianGrid />
            <XAxis
                type="number"
                dataKey="severity"
                name="Weather Severity"
                label={{ value: "Weather Severity Score", position: "bottom" }}
            />
            <YAxis
                type="number"
                dataKey="totalPoints"
                name="Total Points"
                label={{ value: "Total Points", angle: -90, position: "left" }}
            />
            <Tooltip content={<WeatherTooltip />} />

            {/* Outdoor Games */}
            <Scatter
                name="Outdoor"
                data={outdoorGames}
                fill="#2563eb"   // blue
            />

            {/* Dome Games */}
            <Scatter
                name="Dome"
                data={domeGames}
                fill="#16a34a"   // green
            />

            {trendlineData.length > 0 && (
            <Line
                type="linear"
                dataKey="totalPoints"
                data={trendlineData}
                stroke="#dc2626"   // red
                strokeWidth={2}
                dot={false}
                name="Outdoor Trend"
            />
            )}

            </ScatterChart>
        </ResponsiveContainer>
        </div>

        {regression && (
        <p style={{ color: "#444", marginTop: "0.5rem" }}>
            Outdoor trend: total points ≈{" "}
            {regression.slope.toFixed(2)} × severity +{" "}
            {regression.intercept.toFixed(1)}
        </p>
        )}

        <h3>Average Total Points by Weather Severity</h3>

        <table>
        <thead>
            <tr>
            <th>Severity</th>
            <th>Games</th>
            <th>Avg Total Points</th>
            </tr>
        </thead>
        <tbody>
            {bucketStats.map(b => (
            <tr key={b.label}>
                <td>{b.label}</td>
                <td>{b.count}</td>
                <td>{b.avgPoints.toFixed(1)}</td>
            </tr>
            ))}
        </tbody>
        </table>

        <h3>Scoring Impact by Weather Bucket</h3>

        <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
            <BarChart data={bucketStats}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar
                dataKey="avgPoints"
                name="Avg Total Points"
                fill="#2563eb"
            />
            </BarChart>
        </ResponsiveContainer>
        </div>

        <h3>Week-to-Week Comparison</h3>

        <table>
        <thead>
            <tr>
            <th>Week</th>
            <th>Avg Total Points</th>
            <th>Avg Weather Severity (Outdoor)</th>
            <th>Games</th>
            </tr>
        </thead>
        <tbody>
            {comparison.map(w => (
            <tr
                key={w.week}
                style={{
                fontWeight: w.week === week ? "bold" : "normal"
                }}
            >
                <td>Week {w.week}</td>
                <td>{w.avgPoints?.toFixed(1) ?? "N/A"}</td>
                <td>{w.avgSeverity?.toFixed(2) ?? "N/A"}</td>
                <td>{w.games}</td>
            </tr>
            ))}
        </tbody>
        </table>



    </section>
  );
}

export default Analytics;
