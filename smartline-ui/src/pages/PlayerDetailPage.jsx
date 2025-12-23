// src/pages/PlayerDetailPage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, Award, User, MapPin, Calendar, Activity, Target, Zap, Trophy } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';

export default function PlayerDetailPage() {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [gameLog, setGameLog] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(2023);
  const [selectedGameLogStat, setSelectedGameLogStat] = useState('yards');
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(false);
  const [gameLogLoading, setGameLogLoading] = useState(false);
  const [rankingsLoading, setRankingsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPlayerDetails();
  }, [playerId]);

  useEffect(() => {
    if (player) {
      fetchPlayerStatistics(selectedSeason);
      fetchGameLog(selectedSeason);
      fetchPlayerRankings(selectedSeason);
    }
  }, [player, selectedSeason]);

  const fetchPlayerDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/players/${playerId}`);
      
      if (!response.ok) {
        throw new Error('Player not found');
      }
      
      const data = await response.json();
      setPlayer(data);
    } catch (err) {
      console.error('Failed to fetch player:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlayerStatistics = async (season) => {
    try {
      setStatsLoading(true);
      
      const response = await fetch(
        `${API_BASE_URL}/statistics/players/${playerId}/statistics?season=${season}`
      );
      
      if (!response.ok) {
        if (response.status === 404) {
          setStatistics(null);
          setAvailableSeasons([]);
          return;
        }
        throw new Error('Failed to fetch statistics');
      }
      
      const data = await response.json();
      
      // Extract seasons and set statistics
      if (data.seasons && data.seasons.length > 0) {
        const seasons = data.seasons.map(s => s.season).sort((a, b) => b - a);
        setAvailableSeasons(seasons);
        
        // Find the selected season's data
        const seasonData = data.seasons.find(s => s.season === season);
        setStatistics(seasonData || null);
      } else {
        setStatistics(null);
        setAvailableSeasons([]);
      }
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
      setStatistics(null);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchGameLog = async (season) => {
    try {
      setGameLogLoading(true);
      
      // Fetch ALL games without stat_group filter
      const response = await fetch(
        `${API_BASE_URL}/statistics/players/${playerId}/games?season=${season}&limit=10`
      );
      
      if (!response.ok) {
        setGameLog(null);
        return;
      }
      
      const data = await response.json();
      setGameLog(data);
      
      // Set default stat based on position
      if (data.games && data.games.length > 0 && !selectedGameLogStat) {
        const statGroup = getStatGroupForPosition(player?.position);
        const firstGame = data.games[0];
        
        if (firstGame.stat_groups && firstGame.stat_groups[statGroup]) {
          const primaryStats = firstGame.stat_groups[statGroup];
          if (primaryStats && primaryStats.length > 0) {
            const yardsMetric = primaryStats.find(s => s.metric_name === 'yards');
            setSelectedGameLogStat(yardsMetric ? 'yards' : primaryStats[0].metric_name);
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch game log:', err);
      setGameLog(null);
    } finally {
      setGameLogLoading(false);
    }
  };

  const fetchPlayerRankings = async (season) => {
    try {
      setRankingsLoading(true);
      
      const response = await fetch(
        `${API_BASE_URL}/statistics/players/${playerId}/rankings?season=${season}`
      );
      
      if (!response.ok) {
        setRankings([]);
        return;
      }
      
      const data = await response.json();
      
      // Transform the rankings data for display
      const formattedRankings = data.rankings.map(ranking => {
        // Format the metric name for display
        const metricLabel = formatMetricLabel(ranking.metric_name, ranking.stat_group);
        
        // Format the rank with ordinal suffix
        const rankText = formatRankWithOrdinal(ranking.rank);
        
        return {
          label: `${rankText} in ${metricLabel}`,
          value: Math.round(ranking.total_value),
          rank: ranking.rank,
          metric: ranking.metric_name,
          statGroup: ranking.stat_group,
          totalPlayers: ranking.total_players,
          percentile: ranking.percentile
        };
      });
      
      setRankings(formattedRankings);
    } catch (err) {
      console.error('Failed to fetch rankings:', err);
      setRankings([]);
    } finally {
      setRankingsLoading(false);
    }
  };

  const formatMetricLabel = (metricName, statGroup) => {
    const labels = {
      'Passing': {
        'yards': 'Passing Yards',
        'passing touch downs': 'Passing Touchdowns',
        'rating': 'QB Rating',
        'interceptions': 'Interceptions',
        'comp att': 'Completions'
      },
      'Rushing': {
        'yards': 'Rushing Yards',
        'rushing touch downs': 'Rushing Touchdowns',
        'average': 'Yards Per Carry',
        'total rushes': 'Rush Attempts'
      },
      'Receiving': {
        'yards': 'Receiving Yards',
        'receiving touch downs': 'Receiving Touchdowns',
        'receptions': 'Receptions',
        'targets': 'Targets'
      },
      'Defense': {
        'tackles': 'Total Tackles',
        'sacks': 'Sacks',
        'interceptions': 'Interceptions',
        'passes defended': 'Passes Defended',
        'tfl': 'Tackles For Loss',
        'qb hts': 'QB Hits'
      },
      'Kicking': {
        'field goals made': 'Field Goals Made',
        'field goal pct': 'Field Goal %',
        'extra points made': 'Extra Points Made'
      },
      'Punting': {
        'average': 'Punt Average',
        'gross avg': 'Gross Punt Average',
        'inside 20': 'Punts Inside 20'
      }
    };
    
    return labels[statGroup]?.[metricName] || metricName;
  };

  const formatRankWithOrdinal = (rank) => {
    const j = rank % 10;
    const k = rank % 100;
    
    if (j === 1 && k !== 11) {
      return rank + "st";
    }
    if (j === 2 && k !== 12) {
      return rank + "nd";
    }
    if (j === 3 && k !== 13) {
      return rank + "rd";
    }
    return rank + "th";
  };

  const getStatGroupForPosition = (position) => {
    if (!position) return 'Passing';
    
    const positionMap = {
      'QB': 'Passing',
      'RB': 'Rushing',
      'WR': 'Receiving',
      'TE': 'Receiving',
      'K': 'Kicking',
      'P': 'Punting',
      'DB': 'Defense',
      'CB': 'Defense',
      'S': 'Defense',
      'LB': 'Defense',
      'DL': 'Defense',
      'DE': 'Defense',
      'DT': 'Defense',
    };
    
    return positionMap[position] || 'Passing';
  };

  const getKeyMetricsForPosition = (statGroup) => {
    const metricMap = {
      'Passing': [
        { key: 'yards', label: 'Total Passing Yards' },
        { key: 'passing touch downs', label: 'Passing Touchdowns' },
        { key: 'rating', label: 'Average QB Rating' }
      ],
      'Rushing': [
        { key: 'yards', label: 'Total Rushing Yards' },
        { key: 'rushing touch downs', label: 'Rushing Touchdowns' },
        { key: 'average', label: 'Yards Per Carry' }
      ],
      'Receiving': [
        { key: 'yards', label: 'Total Receiving Yards' },
        { key: 'receiving touch downs', label: 'Receiving Touchdowns' },
        { key: 'receptions', label: 'Total Receptions' }
      ],
      'Defense': [
        { key: 'tackles', label: 'Total Tackles' },
        { key: 'sacks', label: 'Total Sacks' },
        { key: 'interceptions', label: 'Total Interceptions' }
      ]
    };
    
    return metricMap[statGroup] || [];
  };

  const getAvailableStatsForGameLog = () => {
    if (!gameLog || !gameLog.games || gameLog.games.length === 0 || !player) return [];
    
    const statGroup = getStatGroupForPosition(player.position);
    const metrics = new Set();
    
    gameLog.games.forEach(game => {
      if (game.stat_groups && game.stat_groups[statGroup]) {
        game.stat_groups[statGroup].forEach(stat => {
          metrics.add(stat.metric_name);
        });
      }
    });
    
    return Array.from(metrics);
  };

  const getGameLogChartData = () => {
    if (!gameLog || !gameLog.games || !player) return [];
    
    const statGroup = getStatGroupForPosition(player.position);
    
    return gameLog.games.map(game => {
      let value = 0;
      
      if (game.stat_groups && game.stat_groups[statGroup]) {
        const stat = game.stat_groups[statGroup].find(s => s.metric_name === selectedGameLogStat);
        if (stat) {
          if (stat.metric_value.includes('/')) {
            const [completed] = stat.metric_value.split('/');
            value = parseFloat(completed) || 0;
          } else if (stat.metric_value.includes('-')) {
            const [num] = stat.metric_value.split('-');
            value = parseFloat(num) || 0;
          } else {
            value = parseFloat(stat.metric_value) || 0;
          }
        }
      }
      
      return {
        date: new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        value: value,
        opponent: game.opponent_abbrev,
        week: game.week
      };
    }).reverse();
  };

  // Helper function for position badge color
  const getPositionColor = (position) => {
    const positionGroups = {
      'QB': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      'RB': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      'WR': 'bg-sky-500/20 text-sky-400 border-sky-500/30',
      'TE': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      'OL': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      'DL': 'bg-red-500/20 text-red-400 border-red-500/30',
      'LB': 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      'DB': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
      'CB': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      'S': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      'K': 'bg-violet-500/20 text-violet-400 border-violet-500/30',
      'P': 'bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30',
    };

    return positionGroups[position] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  // Helper to get icon for stat group
  const getStatGroupIcon = (statGroup) => {
    const icons = {
      'Passing': Activity,
      'Rushing': Zap,
      'Receiving': Target,
      'Defense': Award,
      'Kicking': TrendingUp,
      'Punting': TrendingDown,
      'Returning': ArrowLeft,
      'Scoring': Award,
    };
    return icons[statGroup] || Activity;
  };

  // Helper to format stat value
  const formatStatValue = (value) => {
    if (value === null || value === undefined || value === '') return '-';
    
    // If it's a number, format with commas
    if (!isNaN(value)) {
      return parseFloat(value).toLocaleString();
    }
    
    return value;
  };

  // Helper to safely get a stat value (tries multiple possible field names)
  const getStat = (stats, ...possibleNames) => {
    for (const name of possibleNames) {
      if (stats[name] !== undefined && stats[name] !== null && stats[name] !== '') {
        return stats[name];
      }
    }
    return null;
  };

  // Helper to get key stats based on position
  const getKeyStats = (statGroups) => {
    if (!statGroups) return null;

    const keyStats = [];

    // Passing stats (for QBs)
    if (statGroups['Passing']) {
      const stats = statGroups['Passing'];
      keyStats.push({
        label: 'Pass Yards',
        value: formatStatValue(getStat(stats, 'yards', 'passing yards')),
        icon: Activity
      });
      keyStats.push({
        label: 'Pass TDs',
        value: formatStatValue(getStat(stats, 'passing touchdowns', 'touchdowns')),
        icon: Target
      });
      keyStats.push({
        label: 'Completion %',
        value: stats['completion pct'] ? `${formatStatValue(stats['completion pct'])}%` : '-',
        icon: TrendingUp
      });
      keyStats.push({
        label: 'QB Rating',
        value: formatStatValue(getStat(stats, 'quaterback rating', 'quarterback rating', 'rating')),
        icon: Award
      });
    }

    // Rushing stats (for RBs)
    if (statGroups['Rushing']) {
      const stats = statGroups['Rushing'];
      keyStats.push({
        label: 'Rush Yards',
        value: formatStatValue(getStat(stats, 'yards', 'rushing yards')),
        icon: Zap
      });
      keyStats.push({
        label: 'Rush TDs',
        value: formatStatValue(getStat(stats, 'rushing touchdowns', 'touchdowns')),
        icon: Target
      });
      keyStats.push({
        label: 'Yards/Carry',
        value: formatStatValue(getStat(stats, 'yards per rush avg', 'avg')),
        icon: TrendingUp
      });
      keyStats.push({
        label: 'Rush Attempts',
        value: formatStatValue(getStat(stats, 'rushing attempts', 'attempts')),
        icon: Activity
      });
    }

    // Receiving stats (for WRs, TEs, RBs)
    if (statGroups['Receiving']) {
      const stats = statGroups['Receiving'];
      keyStats.push({
        label: 'Receptions',
        value: formatStatValue(getStat(stats, 'receptions', 'rec')),
        icon: Activity
      });
      keyStats.push({
        label: 'Rec Yards',
        value: formatStatValue(getStat(stats, 'receiving yards', 'yards')),
        icon: Target
      });
      keyStats.push({
        label: 'Rec TDs',
        value: formatStatValue(getStat(stats, 'receiving touchdowns', 'touchdowns')),
        icon: Award
      });
      keyStats.push({
        label: 'Yards/Rec',
        value: formatStatValue(getStat(stats, 'yards per reception avg', 'avg')),
        icon: TrendingUp
      });
    }

    // Defense stats (only show for defensive players)
    if (statGroups['Defense'] && player.player_group === 'Defense') {
      const stats = statGroups['Defense'];
      keyStats.push({
        label: 'Total Tackles',
        value: formatStatValue(getStat(stats, 'total tackles', 'tackles')),
        icon: Activity
      });
      keyStats.push({
        label: 'Sacks',
        value: formatStatValue(getStat(stats, 'sacks')),
        icon: Zap
      });
      keyStats.push({
        label: 'Interceptions',
        value: formatStatValue(getStat(stats, 'interceptions', 'int')),
        icon: Target
      });
      keyStats.push({
        label: 'Pass Defended',
        value: formatStatValue(getStat(stats, 'passes defended', 'pass defended')),
        icon: Award
      });
    }

    return keyStats.length > 0 ? keyStats : null;
  };

  // Helper to filter out irrelevant stat groups
  const getRelevantStatGroups = (statGroups) => {
    if (!statGroups || !player) return statGroups;

    const relevantGroups = {};
    
    // Debug: log player group to see what we're working with
    // console.log('Player Group:', player.player_group);

    // Normalize player_group (trim whitespace, handle case variations)
    const playerGroup = player.player_group ? player.player_group.trim() : null;

    // For offensive players, NEVER show Defense stats
    if (playerGroup === 'Offense') {
      Object.entries(statGroups).forEach(([groupName, stats]) => {
        // Completely exclude Defense for offensive players
        if (groupName !== 'Defense') {
          relevantGroups[groupName] = stats;
        }
      });
    } 
    // For special teams, also exclude Defense
    else if (playerGroup === 'Special Teams') {
      Object.entries(statGroups).forEach(([groupName, stats]) => {
        // Exclude Defense for special teams players
        if (groupName !== 'Defense') {
          relevantGroups[groupName] = stats;
        }
      });
    }
    // For defensive players, exclude offensive stats if minimal
    else if (playerGroup === 'Defense') {
      Object.entries(statGroups).forEach(([groupName, stats]) => {
        // Always include Defense
        if (groupName === 'Defense') {
          relevantGroups[groupName] = stats;
        } else if (groupName === 'Passing' || groupName === 'Rushing' || groupName === 'Receiving') {
          // Only include offensive stats if meaningful (e.g., trick plays)
          const hasStats = Object.values(stats).some(value => 
            value && value !== '0' && value !== 0
          );
          if (hasStats) {
            relevantGroups[groupName] = stats;
          }
        } else {
          // Include other stats like Scoring, Returning, etc.
          relevantGroups[groupName] = stats;
        }
      });
    } else {
      // For unknown/null player groups, default to hiding Defense stats
      // (assume non-defensive player if group is unclear)
      Object.entries(statGroups).forEach(([groupName, stats]) => {
        if (groupName !== 'Defense') {
          relevantGroups[groupName] = stats;
        }
      });
    }

    return relevantGroups;
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6 animate-pulse">
            <div className="w-12 h-12 bg-dark-800 rounded-lg"></div>
            <div className="h-8 w-64 bg-dark-800 rounded"></div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="h-96 bg-dark-800 rounded-xl"></div>
            </div>
            <div className="space-y-6">
              <div className="h-64 bg-dark-800 rounded-xl"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !player) {
    return (
      <div className="min-h-screen bg-dark-950 p-6">
        <div className="max-w-7xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Card className="p-12 text-center">
            <User className="w-16 h-16 mx-auto mb-4 text-slate-600" />
            <h2 className="text-2xl font-bold text-slate-300 mb-2">Player Not Found</h2>
            <p className="text-slate-500">The player you're looking for doesn't exist or has been removed.</p>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        {/* Player Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-start gap-6">
            {/* Player Image */}
            <div className="flex-shrink-0">
              {player.image_url ? (
                <img
                  src={player.image_url}
                  alt={player.full_name}
                  className="w-32 h-32 md:w-40 md:h-40 rounded-xl object-cover border-2 border-dark-700 bg-dark-800"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = '';
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl bg-dark-800 border-2 border-dark-700 flex items-center justify-center">
                  <User className="w-16 h-16 text-slate-600" />
                </div>
              )}
            </div>

            {/* Player Info */}
            <div className="flex-grow">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <h1 className="text-3xl md:text-4xl font-bold text-slate-50">
                  {player.full_name}
                </h1>
                {player.jersey_number && (
                  <span className="text-2xl font-mono font-bold text-primary-400 bg-primary-500/10 px-3 py-1 rounded-lg border border-primary-500/30">
                    #{player.jersey_number}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3 mb-4">
                {player.position && (
                  <Badge className={`${getPositionColor(player.position)} font-mono font-bold text-sm px-3 py-1`}>
                    {player.position}
                  </Badge>
                )}
                {player.team_name && (
                  <Badge variant="outline" className="text-slate-300 border-slate-600 font-medium">
                    <MapPin className="w-3 h-3 mr-1" />
                    {player.team_name}
                  </Badge>
                )}
                {player.player_group && (
                  <Badge variant="outline" className="text-slate-400 border-slate-600">
                    {player.player_group}
                  </Badge>
                )}
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {player.age && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Age</div>
                    <div className="text-lg font-bold text-slate-200">{player.age}</div>
                  </div>
                )}
                {player.experience_years !== null && player.experience_years !== undefined && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Experience</div>
                    <div className="text-lg font-bold text-slate-200">
                      {player.experience_years} {player.experience_years === 1 ? 'year' : 'years'}
                    </div>
                  </div>
                )}
                {player.height && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Height</div>
                    <div className="text-lg font-bold text-slate-200">{player.height}</div>
                  </div>
                )}
                {player.weight && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Weight</div>
                    <div className="text-lg font-bold text-slate-200">{player.weight}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column - Main Info */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Player Details Card */}
            <Card>
              <div className="p-6">
                <h2 className="text-xl font-bold text-slate-50 mb-4 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Player Information
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {player.college && (
                    <div className="border-l-2 border-primary-500 pl-4">
                      <div className="text-sm text-slate-500 mb-1">College</div>
                      <div className="text-base font-semibold text-slate-200">{player.college}</div>
                    </div>
                  )}
                  
                  {player.salary && (
                    <div className="border-l-2 border-emerald-500 pl-4">
                      <div className="text-sm text-slate-500 mb-1">Salary</div>
                      <div className="text-base font-semibold text-emerald-400 font-mono">{player.salary}</div>
                    </div>
                  )}
                  
                  {player.position && (
                    <div className="border-l-2 border-sky-500 pl-4">
                      <div className="text-sm text-slate-500 mb-1">Position</div>
                      <div className="text-base font-semibold text-slate-200">{player.position}</div>
                    </div>
                  )}
                  
                  {player.jersey_number && (
                    <div className="border-l-2 border-violet-500 pl-4">
                      <div className="text-sm text-slate-500 mb-1">Jersey Number</div>
                      <div className="text-base font-semibold text-slate-200 font-mono">#{player.jersey_number}</div>
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Season Statistics */}
            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-slate-50 flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Season Statistics
                  </h2>
                  
                  {/* Season Selector */}
                  {availableSeasons.length > 0 && (
                    <select
                      value={selectedSeason}
                      onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
                      className="bg-dark-800 border border-dark-700 text-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:border-primary-500"
                    >
                      {availableSeasons.map(season => (
                        <option key={season} value={season}>
                          {season} Season
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {statsLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
                    <p className="text-slate-500">Loading statistics...</p>
                  </div>
                ) : statistics && statistics.stat_groups ? (
                  <>
                    {/* Key Stats Highlight */}
                    {getKeyStats(statistics.stat_groups) && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        {getKeyStats(statistics.stat_groups).map((stat, idx) => {
                          const Icon = stat.icon;
                          return (
                            <div key={idx} className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                              <div className="flex items-center gap-2 mb-2">
                                <Icon className="w-4 h-4 text-primary-400" />
                                <div className="text-xs text-slate-500">{stat.label}</div>
                              </div>
                              <div className="text-2xl font-bold text-slate-200">{stat.value}</div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* All Stat Groups (filtered) */}
                    <div className="space-y-4">
                      {Object.entries(getRelevantStatGroups(statistics.stat_groups)).map(([statGroup, stats]) => {
                        const Icon = getStatGroupIcon(statGroup);
                        return (
                          <div key={statGroup} className="border border-dark-700 rounded-lg overflow-hidden">
                            <div className="bg-dark-800/50 px-4 py-3 border-b border-dark-700">
                              <div className="flex items-center gap-2">
                                <Icon className="w-5 h-5 text-primary-400" />
                                <h3 className="font-bold text-slate-200">{statGroup}</h3>
                              </div>
                            </div>
                            <div className="p-4">
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {Object.entries(stats).map(([metricName, metricValue]) => (
                                  <div key={metricName} className="bg-dark-900/30 rounded-lg p-3">
                                    <div className="text-xs text-slate-500 mb-1 capitalize">
                                      {metricName}
                                    </div>
                                    <div className="text-base font-semibold text-slate-200">
                                      {formatStatValue(metricValue)}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Last Updated */}
                    {statistics.last_updated && (
                      <div className="mt-4 text-sm text-slate-500 text-center">
                        Last updated: {new Date(statistics.last_updated).toLocaleDateString()}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-500">No statistics available for this player</p>
                    <p className="text-sm text-slate-600 mt-2">
                      Statistics may not be available for the selected season
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/* Game Log with Chart */}
            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-slate-50 flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Game Log - Last 10 Games
                  </h2>
                  
                  {/* Stat Selector */}
                  {getAvailableStatsForGameLog().length > 0 && (
                    <select
                      value={selectedGameLogStat}
                      onChange={(e) => setSelectedGameLogStat(e.target.value)}
                      className="bg-dark-800 border border-dark-700 text-slate-200 rounded-lg px-4 py-2 focus:outline-none focus:border-primary-500 capitalize"
                    >
                      {getAvailableStatsForGameLog().map(stat => (
                        <option key={stat} value={stat}>
                          {stat}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {gameLogLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
                    <p className="text-slate-500">Loading game log...</p>
                  </div>
                ) : gameLog && gameLog.games && gameLog.games.length > 0 ? (
                  <div className="space-y-6">
                    {/* Chart */}
                    <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                      <div className="h-64 relative">
                        <svg className="w-full h-full" viewBox="0 0 800 250">
                          {/* Y-axis */}
                          <line x1="50" y1="10" x2="50" y2="210" stroke="#475569" strokeWidth="1" />
                          
                          {/* X-axis */}
                          <line x1="50" y1="210" x2="780" y2="210" stroke="#475569" strokeWidth="1" />
                          
                          {/* Chart data */}
                          {(() => {
                            const data = getGameLogChartData();
                            if (data.length === 0) return null;
                            
                            const maxValue = Math.max(...data.map(d => d.value), 1);
                            const xStep = data.length > 1 ? 730 / (data.length - 1) : 0;
                            
                            // Line path
                            const linePath = data.map((d, i) => {
                              const x = 50 + (i * xStep);
                              const y = 210 - ((d.value / maxValue) * 190);
                              return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
                            }).join(' ');
                            
                            return (
                              <>
                                {/* Grid lines */}
                                {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
                                  <g key={i}>
                                    <line 
                                      x1="50" 
                                      y1={210 - (ratio * 190)} 
                                      x2="780" 
                                      y2={210 - (ratio * 190)} 
                                      stroke="#334155" 
                                      strokeWidth="1" 
                                      strokeDasharray="4 4"
                                      opacity="0.3"
                                    />
                                    <text 
                                      x="35" 
                                      y={215 - (ratio * 190)} 
                                      fill="#64748b" 
                                      fontSize="10" 
                                      textAnchor="end"
                                    >
                                      {(maxValue * ratio).toFixed(0)}
                                    </text>
                                  </g>
                                ))}
                                
                                {/* Line */}
                                {data.length > 1 && (
                                  <path 
                                    d={linePath} 
                                    fill="none" 
                                    stroke="#3b82f6" 
                                    strokeWidth="2"
                                  />
                                )}
                                
                                {/* Points and labels */}
                                {data.map((d, i) => {
                                  const x = 50 + (i * xStep);
                                  const y = 210 - ((d.value / maxValue) * 190);
                                  
                                  return (
                                    <g key={i}>
                                      {/* Point */}
                                      <circle 
                                        cx={x} 
                                        cy={y} 
                                        r="4" 
                                        fill="#3b82f6"
                                      />
                                      
                                      {/* Value label */}
                                      <text 
                                        x={x} 
                                        y={y - 10} 
                                        fill="#e2e8f0" 
                                        fontSize="11" 
                                        textAnchor="middle"
                                      >
                                        {d.value.toFixed(0)}
                                      </text>
                                      
                                      {/* X-axis label */}
                                      <text 
                                        x={x} 
                                        y="230" 
                                        fill="#64748b" 
                                        fontSize="10" 
                                        textAnchor="middle"
                                        transform={`rotate(-45 ${x} 230)`}
                                      >
                                        {d.date}
                                      </text>
                                    </g>
                                  );
                                })}
                              </>
                            );
                          })()}
                        </svg>
                      </div>
                    </div>

                    {/* Game List */}
                    <div className="space-y-2">
                      {gameLog.games.slice(0, 10).map((game, idx) => {
                        let statValue = '-';
                        const statGroup = getStatGroupForPosition(player.position);
                        
                        if (game.stat_groups && game.stat_groups[statGroup]) {
                          const stat = game.stat_groups[statGroup].find(s => s.metric_name === selectedGameLogStat);
                          if (stat) {
                            statValue = formatStatValue(stat.metric_value);
                          }
                        }
                        
                        return (
                          <div key={idx} className="bg-dark-900/30 border border-dark-700 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="text-sm text-slate-500 w-24">
                                {new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                              </div>
                              <div className="text-sm font-semibold text-slate-200">
                                vs {game.opponent_abbrev}
                              </div>
                              <div className="text-xs text-slate-500">
                                Week {game.week}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-slate-500 mb-1 capitalize">
                                {selectedGameLogStat}
                              </div>
                              <div className="text-lg font-bold text-primary-400">
                                {statValue}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-500">No game log available</p>
                    <p className="text-sm text-slate-600 mt-2">
                      Game statistics may not be available for this player
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            
            {/* Team Card */}
            {player.team_name && (
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-bold text-slate-50 mb-4">Team</h3>
                  <div className="bg-dark-800/50 rounded-lg p-4 border border-dark-700">
                    <div className="text-2xl font-bold text-slate-200 mb-1">
                      {player.team_name}
                    </div>
                    {player.team_abbrev && (
                      <div className="text-sm text-slate-500 font-mono">
                        {player.team_abbrev}
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            )}

            {/* Season Highlights */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-bold text-slate-50 mb-4 flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  Season Highlights
                </h3>
                
                {rankingsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500 mx-auto mb-3"></div>
                    <p className="text-sm text-slate-500">Loading highlights...</p>
                  </div>
                ) : rankings && rankings.length > 0 ? (
                  <div className="space-y-3">
                    {rankings.map((ranking, idx) => {
                      // Get color based on rank
                      const getRankColor = (rank) => {
                        if (rank === 1) return 'border-yellow-500/70 bg-yellow-500/10';
                        if (rank === 2) return 'border-gray-400/70 bg-gray-400/10';
                        if (rank === 3) return 'border-amber-600/70 bg-amber-600/10';
                        return 'border-primary-500/50 bg-primary-500/10';
                      };
                      
                      const getRankIcon = (rank) => {
                        if (rank === 1) return '🥇';
                        if (rank === 2) return '🥈';
                        if (rank === 3) return '🥉';
                        return '🏆';
                      };
                      
                      return (
                        <div 
                          key={idx} 
                          className={`border-2 rounded-lg p-4 ${getRankColor(ranking.rank)}`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-2xl">{getRankIcon(ranking.rank)}</span>
                            <div className="flex-1">
                              <div className="font-bold text-slate-200 text-lg">
                                {ranking.label}
                              </div>
                              <div className="text-xs text-slate-500">
                                {selectedSeason} Season
                              </div>
                            </div>
                          </div>
                          <div className="ml-10 flex items-baseline gap-3">
                            <div className="text-3xl font-bold text-primary-400">
                              {ranking.value.toLocaleString()}
                            </div>
                            <div className="text-sm text-slate-500">
                              Top {ranking.percentile}%
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Award className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                    <p className="text-sm text-slate-500">No top 10 rankings</p>
                    <p className="text-xs text-slate-600 mt-1">
                      For {selectedSeason} season
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/* Betting Props Placeholder */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-bold text-slate-50 mb-4">Betting Props</h3>
                <div className="text-center py-8">
                  <TrendingUp className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                  <p className="text-sm text-slate-500">Props coming soon</p>
                </div>
              </div>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}
