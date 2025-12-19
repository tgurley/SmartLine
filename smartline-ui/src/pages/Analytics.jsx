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
  LineChart,
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
        <div>
        🏷 Team:{" "}
        <strong>
            {g.label.includes("@")
            ? g.label.split(" @ ").includes(selectedTeam)
                ? selectedTeam
                : "League"
            : "League"}
        </strong>
        </div>


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
  const teamParam = searchParams.get("team") || "";
  const [selectedTeam, setSelectedTeam] = useState(teamParam);


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

  const teamGames = selectedTeam
    ? outdoorGames.filter(
        g =>
            g.label.startsWith(`${selectedTeam} @`) ||
            g.label.endsWith(`@ ${selectedTeam}`)
        )
    : [];


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

    function buildTeamRows(games) {
        const rows = [];

        games.forEach(g => {
            if (!g.result) return;

            const totalSeverity = g.weather.severity_score ?? 0;

            // Away team row
            rows.push({
            team: g.away_team.abbrev,
            pointsFor: g.result.away_score,
            pointsAgainst: g.result.home_score,
            severity: totalSeverity,
            isDome: g.venue?.is_dome
            });

            // Home team row
            rows.push({
            team: g.home_team.abbrev,
            pointsFor: g.result.home_score,
            pointsAgainst: g.result.away_score,
            severity: totalSeverity,
            isDome: g.venue?.is_dome
            });
        });

        return rows;
        }
    
    const teamRows = buildTeamRows(games).filter(r => !r.isDome);

    const teamStatsMap = {};

    teamRows.forEach(r => {
    if (!teamStatsMap[r.team]) {
        teamStatsMap[r.team] = {
        team: r.team,
        games: 0,
        pointsFor: 0,
        pointsAgainst: 0,
        totalSeverity: 0
        };
    }

    const t = teamStatsMap[r.team];
    t.games += 1;
    t.pointsFor += r.pointsFor;
    t.pointsAgainst += r.pointsAgainst;
    t.totalSeverity += r.severity;
    });

    const teamStats = Object.values(teamStatsMap).map(t => ({
    team: t.team,
    games: t.games,
    avgFor: t.pointsFor / t.games,
    avgAgainst: t.pointsAgainst / t.games,
    avgSeverity: t.totalSeverity / t.games
    }));

    const teams = [...new Set(teamStats.map(t => t.team))].sort();
    const displayedTeams = selectedTeam
        ? teamStats.filter(t => t.team === selectedTeam)
        : teamStats;




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

    useEffect(() => {
    setSelectedTeam(teamParam);
    }, [teamParam]);


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

            {/* League baseline (all outdoor games) */}
            <Scatter
            name="League"
            data={outdoorGames}
            fill="#94a3b8"
            opacity={0.5}
            />

            {/* Selected team overlay */}
            {selectedTeam && (
            <Scatter
                name={selectedTeam}
                data={teamGames}
                fill="#2563eb"
            />
            )}

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
        {selectedTeam && (
        <p style={{ fontSize: "0.85rem", color: "#555" }}>
            Highlighted points show <strong>{selectedTeam}</strong> games relative to league-wide outcomes.
        </p>
        )}


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

        <h3>Scoring Trend by Week</h3>

        <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
            <LineChart data={comparison}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Line
                type="monotone"
                dataKey="avgPoints"
                name="Avg Total Points"
                stroke="#2563eb"
                strokeWidth={2}
            />
            </LineChart>
        </ResponsiveContainer>
        </div>

        <h3>Team Performance (Outdoor Games)</h3>

        <label>
        Team:&nbsp;
        <select
            value={selectedTeam}
            onChange={(e) => {
                const newTeam = e.target.value;

                setSearchParams({
                season,
                week,
                ...(newTeam ? { team: newTeam } : {})
                });
            }}
        >
            <option value="">All Teams</option>
            {teams.map(t => (
            <option key={t} value={t}>
                {t}
            </option>
            ))}
        </select>
        </label>


        <table>
        <thead>
            <tr>
            <th>Team</th>
            <th>Games</th>
            <th>Avg Points For</th>
            <th>Avg Points Against</th>
            <th>Avg Severity</th>
            </tr>
        </thead>
        <tbody>
            {displayedTeams
            .sort((a, b) => b.avgFor - a.avgFor)
            .map(t => (
                <tr key={t.team}>
                <td>{t.team}</td>
                <td>{t.games}</td>
                <td>{t.avgFor.toFixed(1)}</td>
                <td>{t.avgAgainst.toFixed(1)}</td>
                <td>{t.avgSeverity.toFixed(2)}</td>
                </tr>
            ))}
        </tbody>
        </table>

        <h3>Avg Points Scored by Team (Outdoor)</h3>

        <div style={{ width: "100%", height: 400 }}>
        <ResponsiveContainer>
            <BarChart data={displayedTeams}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="team" />
            <YAxis />
            <Tooltip />
            <Bar
                dataKey="avgFor"
                name="Avg Points For"
                fill="#2563eb"
            />
            </BarChart>
        </ResponsiveContainer>
        </div>


    </section>
  );
}

export default Analytics;
