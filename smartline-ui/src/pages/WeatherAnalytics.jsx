import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  ScatterChart, Scatter, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingDown, AlertTriangle, Cloud } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const WeatherAnalytics = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const season = searchParams.get('season') || '2023';
  const week = Number(searchParams.get('week')) || 1;
  const selectedTeam = searchParams.get('team') || '';
  
  const [loading, setLoading] = useState(true);
  const [games, setGames] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [teamStats, setTeamStats] = useState([]);
  
  // Fetch weather data
  useEffect(() => {
    const fetchWeatherData = async () => {
      setLoading(true);
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';
        
        // Fetch current week's games
        const gamesResponse = await fetch(`${apiUrl}/games?season=${season}&week=${week}`);
        const gamesData = await gamesResponse.json();
        
        // Transform your data structure to match what we need
        const transformedGames = gamesData.games.map(game => ({
          game_id: game.game_id,
          week: gamesData.week,
          game_datetime_utc: game.kickoff_utc,
          away_team: { abbrev: game.away_team.abbrev, name: game.away_team.name },
          home_team: { abbrev: game.home_team.abbrev, name: game.home_team.name },
          venue: game.venue,
          weather: {
            temp_f: game.weather?.temp_f,
            temp_c: game.weather?.temp_f ? ((game.weather.temp_f - 32) * 5/9) : null,
            wind_mph: game.weather?.wind_mph,
            precip_prob: game.weather?.precip_prob,
            precip_mm: game.weather?.precip_mm,
            weather_severity_score: game.weather?.severity_score || 0,
            is_cold: game.weather?.flags?.cold || false,
            is_hot: false,
            is_windy: game.weather?.flags?.windy || false,
            is_heavy_wind: game.weather?.flags?.heavy_wind || false,
            is_rain_risk: game.weather?.flags?.rain_risk || false,
            is_storm_risk: game.weather?.flags?.storm_risk || false,
          },
          result: game.result
        }));
        
        setGames(transformedGames);
        
        // Fetch all weeks for comparison (for line chart)
        const fetchAllWeeks = async () => {
          const weeklyData = [];
          for (let w = 1; w <= 18; w++) {
            try {
              const weekResponse = await fetch(`${apiUrl}/games?season=${season}&week=${w}`);
              const weekData = await weekResponse.json();
              
              const gamesWithScores = weekData.games.filter(g => g.result);
              const outdoorGames = weekData.games.filter(g => !g.venue?.is_dome);
              
              const avgPoints = gamesWithScores.length > 0
                ? gamesWithScores.reduce((sum, g) => sum + g.result.home_score + g.result.away_score, 0) / gamesWithScores.length
                : 0;
              
              const outdoorWithSeverity = outdoorGames.filter(g => g.weather?.severity_score != null);
              const avgSeverity = outdoorWithSeverity.length > 0
                ? outdoorWithSeverity.reduce((sum, g) => sum + g.weather.severity_score, 0) / outdoorWithSeverity.length
                : 0;
              
              weeklyData.push({
                week: w,
                games: weekData.games.length,
                avgPoints: avgPoints.toFixed(1) || null,
                avgSeverity: avgSeverity || null
              });
            } catch (err) {
              console.error(`Error fetching week ${w}:`, err);
            }
          }
          return weeklyData;
        };
        
        // Fetch weekly comparison in background (don't block main data)
        fetchAllWeeks().then(data => setComparison(data));
        
        setTeamStats([]);
        
      } catch (error) {
        console.error('Error fetching weather data:', error);
        setGames([]);
        setComparison([]);
        setTeamStats([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchWeatherData();
  }, [season, week]);
  
  // Calculate stats from games
  const outdoorGames = games.filter(g => !g.venue?.is_dome);
  const totalPoints = games.map(g => ({
    gameId: g.game_id,
    label: `${g.away_team.abbrev} @ ${g.home_team.abbrev}`,
    totalPoints: g.result ? g.result.home_score + g.result.away_score : null,
    severity: g.weather?.weather_severity_score || 0,
    isDome: g.venue?.is_dome
  })).filter(g => g.totalPoints !== null);
  
  const avgPoints = totalPoints.length > 0
    ? totalPoints.reduce((sum, g) => sum + g.totalPoints, 0) / totalPoints.length
    : 0;
  
  const avgSeverity = outdoorGames.length > 0
    ? outdoorGames.reduce((sum, g) => sum + (g.weather?.weather_severity_score || 0), 0) / outdoorGames.length
    : 0;
  
  const worstGame = outdoorGames.length > 0
    ? outdoorGames.reduce((worst, g) => 
        (g.weather?.weather_severity_score || 0) > (worst.weather?.weather_severity_score || 0) 
          ? g 
          : worst
      )
    : null;
  
  // Severity buckets
  const bucketStats = [
    { label: 'Clear (0)', range: [0, 0] },
    { label: 'Light (1-2)', range: [1, 2] },
    { label: 'Moderate (3-4)', range: [3, 4] },
    { label: 'Severe (5+)', range: [5, 100] }
  ].map(bucket => {
    const gamesInBucket = totalPoints.filter(g => 
      !g.isDome && g.severity >= bucket.range[0] && g.severity <= bucket.range[1]
    );
    return {
      label: bucket.label,
      count: gamesInBucket.length,
      avgPoints: gamesInBucket.length > 0
        ? gamesInBucket.reduce((sum, g) => sum + g.totalPoints, 0) / gamesInBucket.length
        : 0
    };
  });
  
  // Week selector handler
  const handleWeekChange = (newWeek) => {
    setSearchParams({ season, week: newWeek, ...(selectedTeam ? { team: selectedTeam } : {}) });
  };
  
  // Custom tooltip for scatter chart
  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    
    const data = payload[0].payload;
    return (
      <div className="bg-dark-900 border border-dark-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold mb-2">{data.label}</p>
        <div className="space-y-1 text-sm">
          <p className="text-slate-300">
            Total Points: <span className="text-white font-medium">{data.totalPoints}</span>
          </p>
          <p className="text-slate-300">
            Severity: <span className="text-white font-medium">{data.severity}</span>
          </p>
        </div>
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading weather analytics...</div>
      </div>
    );
  }
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Weather Analytics
          </h1>
          <p className="text-slate-400">
            Impact of weather conditions on game outcomes
          </p>
        </div>
        
        {/* Week Selector */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-400">Week:</label>
          <select
            value={week}
            onChange={(e) => handleWeekChange(Number(e.target.value))}
            className="px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {Array.from({ length: 18 }, (_, i) => i + 1).map((w) => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>
        </div>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Card variant="glass">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Avg Total Points</p>
              <p className="text-3xl font-display font-bold text-white">
                {avgPoints.toFixed(1)}
              </p>
            </div>
            <div className="w-12 h-12 bg-primary-500/10 rounded-lg flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-primary-400" />
            </div>
          </div>
        </Card>
        
        <Card variant="glass">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Avg Outdoor Severity</p>
              <p className="text-3xl font-display font-bold text-white">
                {avgSeverity.toFixed(2)}
              </p>
            </div>
            <div className="w-12 h-12 bg-amber-500/10 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
            </div>
          </div>
        </Card>
        
        <Card variant="glass">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Most Extreme Game</p>
              <p className="text-sm font-semibold text-white">
                {worstGame 
                  ? `${worstGame.away_team.abbrev} @ ${worstGame.home_team.abbrev}`
                  : 'N/A'
                }
              </p>
              <p className="text-xs text-slate-500">
                {worstGame 
                  ? `Severity ${worstGame.weather?.weather_severity_score || 0}`
                  : ''
                }
              </p>
            </div>
            <div className="w-12 h-12 bg-red-500/10 rounded-lg flex items-center justify-center">
              <Cloud className="w-6 h-6 text-red-400" />
            </div>
          </div>
        </Card>
      </div>
      
      {/* Scatter Chart: Severity vs Total Points */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Weather Severity vs Total Points</Card.Title>
          <Card.Description>
            Each point represents a game. Outdoor games in blue, dome games in green.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  type="number" 
                  dataKey="severity" 
                  name="Severity"
                  stroke="#94a3b8"
                  label={{ value: 'Weather Severity Score', position: 'bottom', fill: '#94a3b8' }}
                />
                <YAxis 
                  type="number" 
                  dataKey="totalPoints" 
                  name="Total Points"
                  stroke="#94a3b8"
                  label={{ value: 'Total Points', angle: -90, position: 'left', fill: '#94a3b8' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Outdoor games */}
                <Scatter
                  name="Outdoor Games"
                  data={totalPoints.filter(g => !g.isDome)}
                  fill="#0ea5e9"
                />
                
                {/* Dome games */}
                <Scatter
                  name="Dome Games"
                  data={totalPoints.filter(g => g.isDome)}
                  fill="#10b981"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <p className="text-sm text-slate-500 mt-4">
            Higher weather severity generally corresponds to slightly lower total scoring.
          </p>
        </Card.Content>
      </Card>
      
      {/* Bar Chart: Scoring by Severity Bucket */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Average Points by Weather Severity</Card.Title>
          <Card.Description>
            Scoring trends across different weather conditions
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bucketStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Bar dataKey="avgPoints" name="Avg Total Points" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card.Content>
      </Card>
      
      {/* Week-to-Week Comparison */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Week-to-Week Scoring Trends</Card.Title>
          <Card.Description>
            Average total points across the season
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={comparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="week" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="avgPoints" 
                  name="Avg Total Points" 
                  stroke="#0ea5e9" 
                  strokeWidth={2}
                  dot={{ fill: '#0ea5e9' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card.Content>
      </Card>
      
      {/* Weather Severity Scale Reference */}
      <Card variant="glass">
        <Card.Header>
          <Card.Title>Weather Severity Scale</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <Badge variant="success" size="sm" className="mb-2">0</Badge>
              <p className="text-sm text-slate-300">Clear conditions</p>
            </div>
            <div>
              <Badge variant="primary" size="sm" className="mb-2">1-2</Badge>
              <p className="text-sm text-slate-300">Wind or cold present</p>
            </div>
            <div>
              <Badge variant="warning" size="sm" className="mb-2">3-4</Badge>
              <p className="text-sm text-slate-300">Moderate impact</p>
            </div>
            <div>
              <Badge variant="error" size="sm" className="mb-2">5+</Badge>
              <p className="text-sm text-slate-300">High-impact weather</p>
            </div>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default WeatherAnalytics;
