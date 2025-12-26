import { useState, useEffect, useRef } from 'react';
import { Search, DollarSign, Target, TrendingUp, AlertCircle, X, Loader2 } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const LineShoppingTool = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedMarket, setSelectedMarket] = useState('player_pass_yds');
  const [selectedBetType, setSelectedBetType] = useState('over');
  const [searchResults, setSearchResults] = useState([]);
  const [bestOdds, setBestOdds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchRef = useRef(null);

  const API_BASE = 'https://smartline-production.up.railway.app';

  const marketOptions = [
    { key: 'player_pass_yds', label: 'Passing Yards', positions: ['QB'] },
    { key: 'player_pass_tds', label: 'Passing TDs', positions: ['QB'] },
    { key: 'player_rush_yds', label: 'Rushing Yards', positions: ['RB', 'QB'] },
    { key: 'player_reception_yds', label: 'Receiving Yards', positions: ['WR', 'TE', 'RB'] },
    { key: 'player_anytime_td', label: 'Anytime TD', positions: ['RB', 'WR', 'TE', 'QB'] },
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search - exactly like Header.jsx
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchPlayers(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const searchPlayers = async (query) => {
    try {
      setSearchLoading(true);
      
      const response = await fetch(
        `${API_BASE}/players/search?q=${encodeURIComponent(query)}&limit=10`
      );
      
      const data = response.ok ? await response.json() : { results: [] };
      
      setSearchResults(data.results || []);
      setShowDropdown(true);
    } catch (err) {
      console.error('Failed to search players:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  // Fetch best odds when player and market are selected
  useEffect(() => {
    if (!selectedPlayer) {
      setBestOdds([]);
      return;
    }

    const fetchBestOdds = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `${API_BASE}/player-odds/best-odds?player_id=${selectedPlayer.player_id}&market_key=${selectedMarket}&bet_type=${selectedBetType}&season_year=2023&week=18&limit=10`
        );
        
        if (!response.ok) {
          console.warn('Best odds endpoint returned error:', response.status);
          setBestOdds([]);
          return;
        }
        
        const data = await response.json();
        setBestOdds(data);
      } catch (error) {
        console.error('Error fetching best odds:', error);
        setBestOdds([]);
      } finally {
        setLoading(false);
      }
    };

    fetchBestOdds();
  }, [selectedPlayer, selectedMarket, selectedBetType]);

  const handlePlayerSelect = (player) => {
    setSelectedPlayer(player);
    setSearchQuery(player.full_name);
    setShowDropdown(false);
  };

  const clearSelection = () => {
    setSelectedPlayer(null);
    setSearchQuery('');
    setBestOdds([]);
    setSearchResults([]);
  };

  const formatOdds = (american) => {
    if (american > 0) return `+${american}`;
    return `${american}`;
  };

  const calculateImpliedProb = (american) => {
    if (american > 0) {
      return (100 / (american + 100) * 100).toFixed(1);
    }
    return (Math.abs(american) / (Math.abs(american) + 100) * 100).toFixed(1);
  };

  const getBookmakerLogo = (bookmaker) => {
    const colors = {
      'DraftKings': 'from-green-500 to-emerald-600',
      'FanDuel': 'from-blue-500 to-blue-600',
      'BetMGM': 'from-amber-500 to-orange-600',
      'Caesars': 'from-purple-500 to-purple-600',
      'PointsBet': 'from-red-500 to-red-600',
      'BetRivers': 'from-cyan-500 to-blue-600',
      'Unibet': 'from-green-400 to-green-600',
      'WynnBET': 'from-red-600 to-red-700',
    };
    return colors[bookmaker] || 'from-slate-500 to-slate-600';
  };

  const totalResults = searchResults.length;

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 w-full">
          <div>
            <Card.Title className="flex items-center">
              <DollarSign className="w-5 h-5 text-emerald-400 mr-2" />
              Line Shopping Tool
            </Card.Title>
            <Card.Description>
              Compare odds across sportsbooks to find the best value
            </Card.Description>
          </div>
        </div>
      </Card.Header>

      <Card.Content>
        {/* Search and Filters */}
        <div className="space-y-4 mb-6">
          {/* Player Search */}
          <div className="relative" ref={searchRef}>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a player..."
                className="w-full pl-10 pr-10 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
              {selectedPlayer && (
                <button
                  onClick={clearSelection}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              {searchLoading && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-400 animate-spin" />
              )}
            </div>

            {/* Search Dropdown */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute z-10 w-full mt-2 bg-dark-800 border border-dark-700 rounded-lg shadow-xl max-h-64 overflow-y-auto">
                {searchResults.map((player) => (
                  <button
                    key={player.player_id}
                    onClick={() => handlePlayerSelect(player)}
                    className="w-full px-4 py-3 text-left hover:bg-dark-700 transition-colors flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-white font-medium group-hover:text-blue-400">
                        {player.full_name}
                      </p>
                      <p className="text-sm text-slate-400">
                        {player.position} • {player.team_abbrev}
                      </p>
                    </div>
                    <Badge variant="default" size="sm">
                      {player.position}
                    </Badge>
                  </button>
                ))}
              </div>
            )}

            {/* No Results */}
            {showDropdown && searchQuery.trim() && searchResults.length === 0 && !searchLoading && (
              <div className="absolute z-10 w-full mt-2 bg-dark-800 border border-dark-700 rounded-lg shadow-xl p-4">
                <p className="text-slate-400 text-center">No players found</p>
              </div>
            )}
          </div>

          {/* Market and Bet Type Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Market Selection */}
            <div>
              <label className="block text-sm text-slate-400 mb-2">Prop Market</label>
              <select
                value={selectedMarket}
                onChange={(e) => setSelectedMarket(e.target.value)}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors"
              >
                {marketOptions.map((market) => (
                  <option key={market.key} value={market.key}>
                    {market.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Bet Type Selection */}
            <div>
              <label className="block text-sm text-slate-400 mb-2">Bet Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedBetType('over')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                    selectedBetType === 'over'
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg'
                      : 'bg-dark-800 text-slate-400 hover:bg-dark-700 border border-dark-700'
                  }`}
                >
                  Over
                </button>
                <button
                  onClick={() => setSelectedBetType('under')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                    selectedBetType === 'under'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                      : 'bg-dark-800 text-slate-400 hover:bg-dark-700 border border-dark-700'
                  }`}
                >
                  Under
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        {!selectedPlayer ? (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">Search for a player to compare odds</p>
            <p className="text-sm text-slate-500">
              Select a player, market, and bet type to see the best available lines
            </p>
          </div>
        ) : loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-dark-800 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : bestOdds.length === 0 ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">No odds available</p>
            <p className="text-sm text-slate-500">
              This player/market combination doesn't have odds for Week 18, 2023.
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Note: If the endpoint returns 404, the best-odds route may not be deployed yet.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Best Odds Header */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-dark-700">
              <div>
                <h3 className="text-white font-semibold text-lg">
                  {selectedPlayer.full_name}
                </h3>
                <p className="text-sm text-slate-400">
                  {marketOptions.find(m => m.key === selectedMarket)?.label} • Week 18, 2023
                </p>
              </div>
              <Badge variant="primary" size="lg">
                {selectedBetType.toUpperCase()}
              </Badge>
            </div>

            {/* Sportsbook Odds List */}
            {bestOdds.map((odd, index) => {
              const isTopOdds = index === 0;
              
              return (
                <div
                  key={`${odd.best_odds_bookmaker}-${index}`}
                  className={`group relative p-5 rounded-xl transition-all cursor-pointer ${
                    isTopOdds
                      ? 'bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-2 border-emerald-500/50 hover:border-emerald-500'
                      : 'bg-dark-800 border border-dark-700 hover:bg-dark-700 hover:border-blue-500/50'
                  } animate-slide-up`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {isTopOdds && (
                    <div className="absolute -top-3 left-4">
                      <Badge variant="success" size="sm" className="shadow-lg">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        Best Odds
                      </Badge>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    {/* Bookmaker */}
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${getBookmakerLogo(odd.best_odds_bookmaker)} flex items-center justify-center text-white font-bold text-xs shadow-lg`}>
                        {odd.best_odds_bookmaker.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <p className={`font-semibold ${isTopOdds ? 'text-emerald-400' : 'text-white'}`}>
                          {odd.best_odds_bookmaker}
                        </p>
                        <p className="text-sm text-slate-400">
                          Line: {odd.line_value}
                        </p>
                      </div>
                    </div>

                    {/* Odds Display */}
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className={`text-2xl font-bold font-mono ${
                          isTopOdds ? 'text-emerald-400' : 'text-white'
                        }`}>
                          {formatOdds(odd.best_odds_american)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {calculateImpliedProb(odd.best_odds_american)}% implied
                        </p>
                      </div>

                      {/* Rank Badge */}
                      <div className={`w-10 h-10 rounded-full ${
                        isTopOdds 
                          ? 'bg-emerald-500' 
                          : 'bg-dark-900'
                      } flex items-center justify-center text-white font-bold`}>
                        {index + 1}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card.Content>

      {selectedPlayer && bestOdds.length > 0 && (
        <Card.Footer>
          <div className="flex items-center justify-between w-full">
            <div className="text-sm text-slate-400">
              Comparing <span className="text-white font-semibold">{bestOdds.length}</span> sportsbooks
            </div>
            <Button variant="ghost" size="sm">
              View all markets
            </Button>
          </div>
        </Card.Footer>
      )}

      {/* Info Banner */}
      <div className="mx-6 mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-blue-300 font-medium mb-1">
              Week 18, 2023 Historical Data
            </p>
            <p className="text-xs text-blue-400/80">
              Currently showing closing lines from the final week of the 2023 season. 
              Live odds will be integrated in future updates.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default LineShoppingTool;
