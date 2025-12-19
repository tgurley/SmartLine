import { useSearchParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchGames } from "../api/games";

function Analytics() {
  const [searchParams] = useSearchParams();

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
        label: `${g.away_team.abbrev} @ ${g.home_team.abbrev}`
    }));


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

  return (
    <section>
      <Link to={`/games?season=${season}&week=${week}`}>← Back to Games</Link>

      <h2>Analytics — Week {week} ({season})</h2>

      <p>
        Visual breakdown of scoring and weather impact for the selected week.
      </p>

      <label>
        Week:&nbsp;
        <select
            value={week}
            onChange={(e) =>
            setSearchParams({ season, week: Number(e.target.value) })
            }
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


      {/* Charts will go here */}
    </section>
  );
}

export default Analytics;
