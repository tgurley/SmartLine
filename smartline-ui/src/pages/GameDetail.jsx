import { useParams, Link, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchGameDetail } from "../api/gameDetail";

function GameDetail() {
  const { gameId } = useParams();
  const [searchParams] = useSearchParams();

  // Pull context from URL (fallbacks)
  const season = Number(searchParams.get("season")) || 2023;
  const week = Number(searchParams.get("week")) || 1;

  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchGameDetail(gameId);
        setGame(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [gameId]);

  if (loading) return <p>Loading game...</p>;
  if (error) return <p>Error: {error}</p>;
  if (!game) return <p>Game not found.</p>;

  return (
    <section>
      {/* Back keeps your week/season context */}
      <Link to={`/games?season=${season}&week=${week}`}>← Back to Games</Link>

      <h2 className="game-title">
        {game.away_team.name} @ {game.home_team.name}
      </h2>

      <p className="kickoff">
        {new Date(game.kickoff_utc).toLocaleDateString(undefined, {
          weekday: "long",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })}
      </p>

      {game.result && (
        <div className="score-box">
          <span>
            {game.away_team.abbrev} {game.result.away_score}
          </span>
          <span>—</span>
          <span>
            {game.home_team.abbrev} {game.result.home_score}
          </span>
        </div>
      )}

      <h3>Teams</h3>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>Away</th>
            <th>Home</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Team</td>
            <td>{game.away_team.name}</td>
            <td>{game.home_team.name}</td>
          </tr>
        </tbody>
      </table>

      <h3>Weather Impact</h3>
      {game.weather?.source === "dome" ? (
        <p>🏟️ Dome game — no weather impact</p>
      ) : (
        <ul>
          <li>🌡 Temp: {game.weather?.temp_f ?? "N/A"}°F</li>
          <li>💨 Wind: {game.weather?.wind_mph ?? "N/A"} mph</li>

          {game.weather?.precip_mm === null || game.weather?.precip_mm === undefined ? (
            <li>🌧 Rain: N/A</li>
          ) : game.weather?.precip_mm === 0 ? (
            <li>🌧 Rain: None</li>
          ) : (
            <li>🌧 Rain: {game.weather?.precip_mm} mm</li>
          )}

          <li>
            ⚠ Weather Severity: <strong>{game.weather.severity_score ?? 0}</strong>
          </li>

          <div className="weather-explanation">
          <p>
              Weather severity combines temperature, wind, and rain conditions at kickoff.
              Higher scores indicate conditions more likely to impact gameplay.
          </p>

          <ul className="severity-scale">
              <li><strong>0–2:</strong> Minimal impact</li>
              <li><strong>3–5:</strong> Moderate impact</li>
              <li><strong>6+:</strong> High impact</li>
          </ul>

          <p className="why-it-matters">
              ⚡ Games with higher weather severity often see lower scoring
              and increased variance.
          </p>
          </div>

        </ul>
      )}

      <h3>Odds</h3>
      <p>Odds data coming soon.</p>

      <h3>Team Stats</h3>
      <p>Advanced stats coming soon.</p>

      <h3>Game ID (for testing)</h3>
      <p>Game ID: {gameId}</p>
    </section>
  );
}

export default GameDetail;
