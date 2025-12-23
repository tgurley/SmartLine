// src/pages/TeamDetailPage.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Users, MapPin, Trophy, Calendar, Activity, ChevronDown } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';

export default function TeamDetailPage() {
  const { teamId } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [roster, setRoster] = useState([]);
  const [seasonStats, setSeasonStats] = useState(null);
  const [recentGames, setRecentGames] = useState([]);
  const [standings, setStandings] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2023);
  const [availableSeasons] = useState([2023, 2024]);
  const [collapsedSections, setCollapsedSections] = useState({
    'Offense': true,
    'Defense': true,
    'Injured Reserve Or O': true,
    'Practice Squad': true
  });
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(false);
  const [gamesLoading, setGamesLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTeamDetails();
  }, [teamId]);

  useEffect(() => {
    if (team) {
      fetchSeasonStats(selectedSeason);
      fetchRecentGames(selectedSeason);
      fetchStandings(selectedSeason);
    }
  }, [team, selectedSeason]);

  const fetchTeamDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch team details
      const teamResponse = await fetch(`${API_BASE_URL}/teams/${teamId}`);
      if (!teamResponse.ok) {
        throw new Error('Team not found');
      }
      const teamData = await teamResponse.json();
      setTeam(teamData);
      
      // Fetch roster
      const rosterResponse = await fetch(`${API_BASE_URL}/teams/${teamId}/roster`);
      if (rosterResponse.ok) {
        const rosterData = await rosterResponse.json();
        setRoster(rosterData.players || []);
      }
    } catch (err) {
      console.error('Failed to fetch team:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSeasonStats = async (season) => {
    try {
      setStatsLoading(true);
      
      // Fetch team's game-by-game stats
      const response = await fetch(
        `${API_BASE_URL}/statistics/teams/${teamId}/games?season=${season}&limit=100`
      );
      
      if (!response.ok) {
        setSeasonStats(null);
        return;
      }
      
      const data = await response.json();
      const games = data.games || [];
      
      if (games.length === 0) {
        setSeasonStats(null);
        return;
      }
      
      // Calculate season aggregates
      const wins = games.filter(g => g.result === 'W').length;
      const losses = games.filter(g => g.result === 'L').length;
      const ties = games.filter(g => g.result === 'T').length;
      
      const totalPoints = games.reduce((sum, g) => sum + (g.team_score || 0), 0);
      const totalYards = games.reduce((sum, g) => sum + (g.total_yards || 0), 0);
      const totalPassYards = games.reduce((sum, g) => sum + (g.passing_yards || 0), 0);
      const totalRushYards = games.reduce((sum, g) => sum + (g.rushing_yards || 0), 0);
      const totalPointsAllowed = games.reduce((sum, g) => sum + (g.opponent_score || 0), 0);
      
      // Calculate yards allowed if available
      let totalYardsAllowed = 0;
      let hasYardsAllowed = false;
      games.forEach(g => {
        if (g.yards_allowed && g.yards_allowed > 0) {
          totalYardsAllowed += g.yards_allowed;
          hasYardsAllowed = true;
        }
      });
      
      const stats = {
        record: ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`,
        wins,
        losses,
        ties,
        gamesPlayed: games.length,
        pointsPerGame: (totalPoints / games.length).toFixed(1),
        yardsPerGame: (totalYards / games.length).toFixed(1),
        passYardsPerGame: (totalPassYards / games.length).toFixed(1),
        rushYardsPerGame: (totalRushYards / games.length).toFixed(1),
        pointsAllowedPerGame: (totalPointsAllowed / games.length).toFixed(1),
        yardsAllowedPerGame: hasYardsAllowed ? (totalYardsAllowed / games.length).toFixed(1) : null,
        // Placeholders for rankings - will be filled by fetchRankings
        pointsRank: null,
        yardsRank: null,
        passYardsRank: null,
        rushYardsRank: null,
        pointsAllowedRank: null,
        yardsAllowedRank: null,
        divisionPlacement: null
      };
      
      setSeasonStats(stats);
      
      // Fetch rankings
      await fetchTeamRankings(season, stats);
    } catch (err) {
      console.error('Failed to fetch season stats:', err);
      setSeasonStats(null);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchTeamRankings = async (season, stats) => {
    try {
      const categories = [
        { key: 'points', stat: 'pointsPerGame', rankKey: 'pointsRank' },
        { key: 'yards_total', stat: 'yardsPerGame', rankKey: 'yardsRank' },
        { key: 'passing_yards', stat: 'passYardsPerGame', rankKey: 'passYardsRank' },
        { key: 'rushing_yards', stat: 'rushYardsPerGame', rankKey: 'rushYardsRank' },
        { key: 'points_allowed', stat: 'pointsAllowedPerGame', rankKey: 'pointsAllowedRank' }
      ];
      
      for (const category of categories) {
        try {
          const url = `${API_BASE_URL}/statistics/teams/leaders/${category.key}?season=${season}&limit=32`;
          console.log(`Fetching: ${url}`);
          
          const response = await fetch(url);
          
          console.log(`Response status for ${category.key}:`, response.status);
          
          if (response.ok) {
            const leaders = await response.json();
            console.log(`Leaders for ${category.key}:`, leaders.length, 'teams');
            
            const rank = leaders.findIndex(t => t.team_id === parseInt(teamId)) + 1;
            
            if (rank > 0) {
              console.log(`Rank for ${category.key}: #${rank}`);
              setSeasonStats(prev => ({
                ...prev,
                [category.rankKey]: rank
              }));
            }
          } else {
            const errorText = await response.text();
            console.error(`Error ${response.status} for ${category.key}:`, errorText);
          }
        } catch (err) {
          console.error(`Failed to fetch ${category.key} rankings:`, err);
        }
      }
      
    } catch (err) {
      console.error('Failed to fetch team rankings:', err);
    }
  };

  const fetchStandings = async (season) => {
    try {
      const url = `${API_BASE_URL}/statistics/teams/${teamId}/standings?season=${season}`;
      console.log(`Fetching standings: ${url}`);
      
      const response = await fetch(url);
      
      console.log(`Standings response status:`, response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Standings data:', data);
        setStandings(data);
      } else {
        const errorText = await response.text();
        console.error(`Standings error ${response.status}:`, errorText);
      }
    } catch (err) {
      console.error('Failed to fetch standings:', err);
    }
  };

  const fetchRecentGames = async (season) => {
    try {
      setGamesLoading(true);
      
      const response = await fetch(
        `${API_BASE_URL}/statistics/teams/${teamId}/games?season=${season}&limit=10`
      );
      
      if (!response.ok) {
        setRecentGames([]);
        return;
      }
      
      const data = await response.json();
      setRecentGames(data.games || []);
    } catch (err) {
      console.error('Failed to fetch recent games:', err);
      setRecentGames([]);
    } finally {
      setGamesLoading(false);
    }
  };

  const toggleSection = (sectionName) => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
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
  if (error || !team) {
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
            <Users className="w-16 h-16 mx-auto mb-4 text-slate-600" />
            <h2 className="text-2xl font-bold text-slate-300 mb-2">Team Not Found</h2>
            <p className="text-slate-500">The team you're looking for doesn't exist.</p>
          </Card>
        </div>
      </div>
    );
  }

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

  // Group roster by position group with proper ordering
  const rosterByGroup = roster.reduce((acc, player) => {
    const group = player.player_group || 'Other';
    if (!acc[group]) acc[group] = [];
    acc[group].push(player);
    return acc;
  }, {});

  // Define the exact order for roster groups
  const rosterGroupOrder = ['Offense', 'Defense', 'Injured Reserve Or O', 'Practice Squad'];
  
  const orderedRosterGroups = rosterGroupOrder
    .filter(group => rosterByGroup[group])
    .map(group => ({ group, players: rosterByGroup[group] }));

  // Add any remaining groups not in the defined order
  Object.entries(rosterByGroup).forEach(([group, players]) => {
    if (!rosterGroupOrder.includes(group)) {
      orderedRosterGroups.push({ group, players });
    }
  });

  const getRankDisplay = (rank) => {
    if (!rank) return 'N/A';
    
    const suffix = (rank) => {
      const j = rank % 10;
      const k = rank % 100;
      if (j === 1 && k !== 11) return "st";
      if (j === 2 && k !== 12) return "nd";
      if (j === 3 && k !== 13) return "rd";
      return "th";
    };
    
    return `${rank}${suffix(rank)}`;
  };

  const getRankColor = (rank) => {
    if (!rank) return 'text-slate-500';
    if (rank <= 5) return 'text-emerald-400';
    if (rank <= 10) return 'text-sky-400';
    if (rank <= 20) return 'text-amber-400';
    return 'text-slate-400';
  };

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

        {/* Team Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            {/* Team Logo */}
            <div className="flex-shrink-0">
              {team.logo_url ? (
                <img
                  src={team.logo_url}
                  alt={`${team.name} logo`}
                  className="w-32 h-32 md:w-40 md:h-40 rounded-xl object-contain bg-dark-900 border-2 border-dark-700 p-4"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextElementSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div 
                className="w-32 h-32 md:w-40 md:h-40 rounded-xl bg-gradient-primary flex items-center justify-center border-2 border-primary-500/30"
                style={{ display: team.logo_url ? 'none' : 'flex' }}
              >
                <span className="text-6xl font-bold text-white">{team.abbrev}</span>
              </div>
            </div>

            {/* Team Info */}
            <div className="flex-grow">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <h1 className="text-3xl md:text-4xl font-bold text-slate-50">
                  {team.name}
                </h1>
              </div>

              <div className="flex flex-wrap items-center gap-3 mb-4">
                <Badge variant="outline" className="text-slate-300 border-slate-600 font-medium text-sm px-3 py-1">
                  <MapPin className="w-3 h-3 mr-1" />
                  {team.city || team.abbrev}
                </Badge>
                <Badge className="bg-primary-500/20 text-primary-400 border-primary-500/30 font-mono font-bold text-sm px-3 py-1">
                  {team.abbrev}
                </Badge>
                {team.established && (
                  <Badge variant="outline" className="text-slate-400 border-slate-600 text-sm px-3 py-1">
                    Est. {team.established}
                  </Badge>
                )}
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {team.stadium && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Stadium</div>
                    <div className="text-sm font-semibold text-slate-200 truncate">{team.stadium}</div>
                  </div>
                )}
                
                {team.coach && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Head Coach</div>
                    <div className="text-sm font-semibold text-slate-200 truncate">{team.coach}</div>
                  </div>
                )}
                
                <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">Roster Size</div>
                  <div className="text-lg font-bold text-slate-200">{roster.length}</div>
                </div>
                
                {team.owner && (
                  <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-1">Owner</div>
                    <div className="text-sm font-semibold text-slate-200 truncate">{team.owner}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid - Mobile First, Desktop Last */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT COLUMN (Desktop) / TOP SECTION (Mobile) - Stats & Games */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Season Stats */}
            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-slate-50 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Season Stats
                  </h3>
                  
                  {/* Season Selector */}
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
                </div>

                {statsLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
                    <p className="text-slate-500">Loading statistics...</p>
                  </div>
                ) : seasonStats ? (
                  <div className="space-y-4">
                    {/* Record with Conference & Division */}
                    <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                      <div className="text-sm text-slate-500 mb-1">Record</div>
                      <div className="flex items-center gap-4 flex-wrap">
                        <div className="text-3xl font-bold text-slate-200">{seasonStats.record}</div>
                        
                        {standings && standings.conference_rank && (
                          <div className="flex items-center gap-2">
                            <div className="text-sm text-slate-500">
                              {standings.conference}
                            </div>
                            <div className={`text-sm font-bold ${getRankColor(standings.conference_rank)}`}>
                              #{standings.conference_rank}
                            </div>
                          </div>
                        )}
                        
                        {standings && standings.division_rank && standings.division && (
                          <div className="flex items-center gap-2">
                            <div className="text-sm text-slate-500">
                              {standings.division}
                            </div>
                            <div className={`text-sm font-bold ${getRankColor(standings.division_rank)}`}>
                              #{standings.division_rank}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Points per Game */}
                      <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                        <div className="text-sm text-slate-500 mb-2">
                          Points per Game {seasonStats.pointsRank && (
                            <span className={`font-bold ${getRankColor(seasonStats.pointsRank)}`}>
                              Ranked #{seasonStats.pointsRank}
                            </span>
                          )}
                        </div>
                        <div className="text-3xl font-bold text-primary-400">{seasonStats.pointsPerGame}</div>
                      </div>

                      {/* Total Yards per Game */}
                      <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                        <div className="text-sm text-slate-500 mb-2">
                          Total Yards per Game {seasonStats.yardsRank && (
                            <span className={`font-bold ${getRankColor(seasonStats.yardsRank)}`}>
                              Ranked #{seasonStats.yardsRank}
                            </span>
                          )}
                        </div>
                        <div className="text-3xl font-bold text-primary-400">{seasonStats.yardsPerGame}</div>
                      </div>

                      {/* Passing Yards per Game */}
                      <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                        <div className="text-sm text-slate-500 mb-2">
                          Passing Yards per Game {seasonStats.passYardsRank && (
                            <span className={`font-bold ${getRankColor(seasonStats.passYardsRank)}`}>
                              Ranked #{seasonStats.passYardsRank}
                            </span>
                          )}
                        </div>
                        <div className="text-3xl font-bold text-primary-400">{seasonStats.passYardsPerGame}</div>
                      </div>

                      {/* Rushing Yards per Game */}
                      <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                        <div className="text-sm text-slate-500 mb-2">
                          Rushing Yards per Game {seasonStats.rushYardsRank && (
                            <span className={`font-bold ${getRankColor(seasonStats.rushYardsRank)}`}>
                              Ranked #{seasonStats.rushYardsRank}
                            </span>
                          )}
                        </div>
                        <div className="text-3xl font-bold text-primary-400">{seasonStats.rushYardsPerGame}</div>
                      </div>

                      {/* Points Allowed per Game */}
                      <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                        <div className="text-sm text-slate-500 mb-2">
                          Points Allowed per Game {seasonStats.pointsAllowedRank && (
                            <span className={`font-bold ${getRankColor(seasonStats.pointsAllowedRank)}`}>
                              Ranked #{seasonStats.pointsAllowedRank}
                            </span>
                          )}
                        </div>
                        <div className="text-3xl font-bold text-red-400">{seasonStats.pointsAllowedPerGame}</div>
                      </div>

                      {/* Total Yards Allowed per Game */}
                      {seasonStats.yardsAllowedPerGame && (
                        <div className="bg-dark-900/50 border border-dark-700 rounded-lg p-4">
                          <div className="text-sm text-slate-500 mb-2">
                            Yards Allowed per Game {seasonStats.yardsAllowedRank && (
                              <span className={`font-bold ${getRankColor(seasonStats.yardsAllowedRank)}`}>
                                Ranked #{seasonStats.yardsAllowedRank}
                              </span>
                            )}
                          </div>
                          <div className="text-3xl font-bold text-red-400">{seasonStats.yardsAllowedPerGame}</div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-500">No statistics available</p>
                    <p className="text-sm text-slate-600 mt-2">
                      Statistics may not be available for the selected season
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/* Recent Games */}
            <Card>
              <div className="p-6">
                <h3 className="text-xl font-bold text-slate-50 mb-6 flex items-center gap-2">
                  <Trophy className="w-5 h-5" />
                  Recent Games
                </h3>

                {gamesLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
                    <p className="text-slate-500">Loading games...</p>
                  </div>
                ) : recentGames.length > 0 ? (
                  <div className="space-y-3">
                    {recentGames.map((game, idx) => (
                      <div 
                        key={idx} 
                        className="bg-dark-900/50 border border-dark-700 rounded-lg p-4 hover:border-dark-600 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className={`px-2 py-1 rounded font-bold text-sm ${
                              game.result === 'W' 
                                ? 'bg-emerald-500/20 text-emerald-400' 
                                : game.result === 'L'
                                ? 'bg-red-500/20 text-red-400'
                                : 'bg-slate-500/20 text-slate-400'
                            }`}>
                              {game.result}
                            </div>
                            <div className="text-sm text-slate-500">
                              Week {game.week}
                            </div>
                            <div className="text-sm text-slate-500">
                              {new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </div>
                          </div>
                          <div className="text-sm font-mono text-slate-400">
                            {game.is_home ? 'vs' : '@'} {game.opponent_abbrev}
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div className="text-2xl font-bold text-slate-200">
                            {game.team_score} - {game.opponent_score}
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-slate-500">Total Yards</div>
                            <div className="text-sm font-semibold text-slate-300">{game.total_yards}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-500">No recent games available</p>
                  </div>
                )}
              </div>
            </Card>

          </div>

          {/* RIGHT COLUMN (Desktop) / BOTTOM SECTION (Mobile) - Roster */}
          <div className="space-y-6">
            
            {/* Schedule Placeholder */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-bold text-slate-50 mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Schedule
                </h3>
                <div className="text-center py-8">
                  <Calendar className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                  <p className="text-sm text-slate-500">Schedule coming soon</p>
                </div>
              </div>
            </Card>

            {/* Rosters Card - All position groups in one card */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-bold text-slate-50 mb-6 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Rosters
                </h3>
                
                {orderedRosterGroups.length > 0 ? (
                  <div className="space-y-4">
                    {orderedRosterGroups.map(({ group, players }) => {
                      const isCollapsed = collapsedSections[group] !== false;
                      
                      return (
                        <div key={group} className="border border-dark-700 rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleSection(group)}
                            className="w-full flex items-center justify-between p-4 bg-dark-800/30 hover:bg-dark-800/50 transition-colors"
                          >
                            <h4 className="text-base font-bold text-slate-50 flex items-center gap-2">
                              {group} ({players.length})
                            </h4>
                            <ChevronDown 
                              className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${
                                isCollapsed ? '' : 'rotate-180'
                              }`}
                            />
                          </button>
                          
                          {!isCollapsed && (
                            <div className="p-4 space-y-2 bg-dark-900/20">
                              {players.map((player) => (
                                <button
                                  key={player.player_id}
                                  onClick={() => navigate(`/players/${player.player_id}`)}
                                  className="w-full flex items-center gap-3 p-3 bg-dark-800/50 hover:bg-dark-800 border border-dark-700 rounded-lg transition-all text-left group"
                                >
                                  {player.image_url ? (
                                    <img
                                      src={player.image_url}
                                      alt={player.full_name}
                                      className="w-10 h-10 rounded-lg object-cover border border-dark-700 flex-shrink-0"
                                      onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.style.display = 'none';
                                      }}
                                    />
                                  ) : (
                                    <div className="w-10 h-10 rounded-lg bg-dark-700 border border-dark-600 flex items-center justify-center flex-shrink-0">
                                      <Users className="w-5 h-5 text-slate-600" />
                                    </div>
                                  )}
                                  
                                  <div className="flex-grow min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="font-semibold text-slate-200 truncate group-hover:text-primary-400 transition-colors text-sm">
                                        {player.full_name}
                                      </span>
                                      {player.jersey_number && (
                                        <span className="text-xs font-mono font-bold text-slate-500 flex-shrink-0">
                                          #{player.jersey_number}
                                        </span>
                                      )}
                                    </div>
                                    {player.position && (
                                      <div className="mt-1">
                                        <Badge className={`${getPositionColor(player.position)} text-xs px-2 py-0.5`}>
                                          {player.position}
                                        </Badge>
                                      </div>
                                    )}
                                  </div>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Users className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                    <p className="text-sm text-slate-500">No roster data available</p>
                  </div>
                )}
              </div>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}
