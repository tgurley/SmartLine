import { useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchGames } from "../api/games";

function GamesDashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // URL-driven state (authoritative)
  const season = Number(searchParams.get("season")) || 2023;
  const week = Number(searchParams.get("week")) || 1;

  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchGames(season, week);
        setGames(data.games);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [season, week]);

  // Update URL when week changes
  const handleWeekChange = (newWeek) => {
    setSearchParams({ season, week: newWeek });
  };

  return (
    <section>
      <h2>
        Week {week} Games <span style={{ color: "#666" }}>({season})</span>
      </h2>

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

      {loading && <p>Loading games...</p>}
      {error && <p>Error: {error}</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th className="col-kickoff">Kickoff</th>
                <th>Away</th>
                <th>Home</th>
                <th className="col-status">Status</th>
                <th className="col-weather">Weather</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {games.map((g) => (
                <tr key={g.game_id}>
                  <td className="col-kickoff">
                    {new Date(g.kickoff_utc).toLocaleDateString(undefined, {
                      weekday: "short",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </td>
                  <td>{g.away_team.abbrev}</td>
                  <td>{g.home_team.abbrev}</td>
                  <td className="col-status">
                    <span className={`status status-${g.status}`}>
                      {g.status}
                    </span>
                  </td>
                  <td className="col-weather">
                    {g.weather.severity_score > 0 ? (
                      <span className="weather-badge">
                        ⚠ {g.weather.severity_score}
                      </span>
                    ) : (
                      <span className="weather-clear">Clear</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="view-btn"
                      onClick={() => navigate(`/game/${g.game_id}?season=${season}&week=${week}`)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default GamesDashboard;
