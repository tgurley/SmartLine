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
  ResponsiveContainer
} from "recharts";


function Analytics() {
  const [searchParams, setSearchParams] = useSearchParams();


  const season = Number(searchParams.get("season")) || 2023;
  const week = Number(searchParams.get("week")) || 1;

  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);

  const totals = games
    .filter(g => g.result)
    .map(g => ({
        gameId: g.game_id,
        totalPoints: g.result.home_score + g.result.away_score,
        severity: g.weather.severity_score,
        isDome: g.venue?.is_dome,
        label: `${g.away_team.abbrev} @ ${g.home_team.abbrev}`
    }));

  const domeGames = totals.filter(g => g.isDome);
  const outdoorGames = totals.filter(g => !g.isDome);


  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await fetchGames(season, week);
      setGames(data.games);
      setLoading(false);
    }

    load();
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
            <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(value, name, props) => {
                if (name === "totalPoints") return [`${value}`, "Total Points"];
                if (name === "severity") return [`${value}`, "Severity"];
                return value;
                }}
                labelFormatter={(_, payload) =>
                payload?.[0]?.payload?.label ?? ""
                }
            />
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
            </ScatterChart>
        </ResponsiveContainer>
        </div>

    </section>
  );
}

export default Analytics;
