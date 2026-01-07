import { useState, useEffect, useRef } from 'react';
import { X, Search, User, Loader2, Plus, TrendingUp } from 'lucide-react';
import Button from '../ui/Button';
import { 
  getPlayerMarkets, 
  getTeamMarkets, 
  getBetType,
  marketRequiresLine,
  POSITIONS_BY_SPORT 
} from '../../constants/bettingMarkets';

const API_BASE = 'https://smartline-production.up.railway.app';

const AddBetModal = ({ onClose, onBetAdded, accounts }) => {
  // Tab state
  const [betMode, setBetMode] = useState('single'); // 'single' or 'parlay'
  
  // Single bet state
  const [formData, setFormData] = useState({
    account_id: accounts.length > 0 ? accounts[0].account_id : null,
    bet_type: 'player_prop',
    sport: 'NFL',
    player_id: null,
    market_key: 'player_pass_yds',
    bet_side: 'over',
    line_value: '',
    odds_american: '',
    stake_amount: '',
    notes: ''
  });
  
  // Parlay state
  const [parlayLegs, setParlayLegs] = useState([createEmptyLeg()]);
  const [parlayStake, setParlayStake] = useState('');
  const [parlayNotes, setParlayNotes] = useState('');
  const [parlayAccount, setParlayAccount] = useState(accounts.length > 0 ? accounts[0].account_id : null);
  
  const [selectedAccountBalance, setSelectedAccountBalance] = useState(
    accounts.length > 0 ? parseFloat(accounts[0].current_balance) : 0
  );
  const [playerSearch, setPlayerSearch] = useState('');
  const [playerResults, setPlayerResults] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchType, setSearchType] = useState('player'); // 'player' or 'team'
  const [teamSearch, setTeamSearch] = useState('');
  const [teamResults, setTeamResults] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  const searchRef = useRef(null);
  const modalRef = useRef(null);

  function createEmptyLeg() {
    return {
      id: Date.now() + Math.random(),
      bet_type: 'player_prop',
      sport: 'NFL',
      market_key: 'player_pass_yds',
      bet_side: 'over',
      line_value: '',
      odds_american: -110,
      player_id: null,
      game_id: null,
      notes: ''
    };
  }

  // Calculate parlay odds
  const combinedOdds = calculateParlayOdds(parlayLegs);
  const parlayPayout = parlayStake ? calculatePayout(parseFloat(parlayStake), combinedOdds) : 0;

  function calculateParlayOdds(legs) {
    if (legs.some(leg => !leg.odds_american)) return 0;

    const decimalOdds = legs.map(leg => {
      const american = parseInt(leg.odds_american);
      if (american > 0) {
        return (american / 100) + 1;
      } else {
        return (100 / Math.abs(american)) + 1;
      }
    });

    const combinedDecimal = decimalOdds.reduce((acc, odds) => acc * odds, 1);

    if (combinedDecimal >= 2.0) {
      return Math.round((combinedDecimal - 1) * 100);
    } else {
      return Math.round(-100 / (combinedDecimal - 1));
    }
  }

  function calculatePayout(stake, americanOdds) {
    if (americanOdds > 0) {
      return stake * (1 + americanOdds / 100);
    } else {
      return stake * (1 + 100 / Math.abs(americanOdds));
    }
  }

  function addParlayLeg() {
    if (parlayLegs.length >= 15) {
      alert('Maximum 15 legs per parlay');
      return;
    }
    setParlayLegs([...parlayLegs, createEmptyLeg()]);
  }

  function removeParlayLeg(index) {
    if (parlayLegs.length <= 2) {
      alert('Parlay must have at least 2 legs');
      return;
    }
    setParlayLegs(parlayLegs.filter((_, i) => i !== index));
  }

  function updateParlayLeg(index, field, value) {
    const newLegs = [...parlayLegs];
    newLegs[index] = { ...newLegs[index], [field]: value };
    setParlayLegs(newLegs);
  }

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

  // Debounced player search
  useEffect(() => {
    if (!playerSearch.trim()) {
      setPlayerResults([]);
      setShowDropdown(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchPlayers(playerSearch);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [playerSearch]);

  const searchPlayers = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setPlayerResults([]);
      return;
    }

    try {
      setSearching(true);
      
      const response = await fetch(
        `${API_BASE}/players/search?q=${encodeURIComponent(searchQuery)}&sport=${formData.sport}&limit=10`
      );
      
      if (response.ok) {
        const data = await response.json();
        
        // ⭐ MAP API FIELDS → UI FIELDS
        const mappedResults = (data.results || []).map(player => ({
          player_id: player.player_id,
          player_name: player.full_name,           // ← full_name → player_name
          position: player.position,
          team_abbreviation: player.abbrev,        // ← abbrev → team_abbreviation
          team_logo_url: player.team_logo_url,
          sport: formData.sport
        }));
        
        setPlayerResults(mappedResults);
      }
    } catch (error) {
      console.error('Error searching players:', error);
      setPlayerResults([]);
    } finally {
      setSearching(false);
    }
  };

  const searchTeams = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setTeamResults([]);
      return;
    }

    try {
      setSearching(true);
      
      const response = await fetch(
        `${API_BASE}/teams/search?q=${encodeURIComponent(searchQuery)}&sport=${formData.sport}&limit=10`
      );
      
      if (response.ok) {
        const data = await response.json();
        
        // ⭐ MAP API FIELDS → UI FIELDS
        const mappedResults = (data.results || []).map(team => ({
          team_id: team.team_id,
          name: team.name,
          city: team.city || '',
          abbreviation: team.abbrev,               // ← abbrev → abbreviation
          logo_url: team.logo_url,
          sport: formData.sport
        }));
        
        setTeamResults(mappedResults);
      }
    } catch (error) {
      console.error('Error searching teams:', error);
      setTeamResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleTeamSelect = (team) => {
    setSelectedTeam(team);
    setTeamSearch(`${team.city} ${team.name}`);
    setShowDropdown(false);
    
    // Update form data
    setFormData({
      ...formData,
      bet_type: 'team_prop',
      team_id: team.team_id,
      player_id: null,
      market_key: 'h2h' // Default to moneyline
    });
    
    setSelectedPlayer(null);
  };

  const handlePlayerSelect = (player) => {
    setSelectedPlayer(player);
    setFormData({ ...formData, player_id: player.player_id });
    setPlayerSearch(player.player_name);
    setShowDropdown(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });

    if (name === 'account_id' && value) {
      const account = accounts.find(acc => acc.account_id === parseInt(value));
      if (account) {
        setSelectedAccountBalance(parseFloat(account.current_balance));
      }
    }
  };

  const getAvailableMarkets = () => {
    // If team is selected
    if (selectedTeam) {
      return getTeamMarkets(formData.sport);
    }
    
    // If player is selected
    if (selectedPlayer) {
      const position = selectedPlayer.position;
      return getPlayerMarkets(formData.sport, position);
    }
    
    // Default: show player markets for selected sport
    return getPlayerMarkets(formData.sport, null);
  };

  const availableMarkets = getAvailableMarkets();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (betMode === 'single') {
      await submitSingleBet();
    } else {
      await submitParlay();
    }
  };

  const submitSingleBet = async () => {
    const stakeAmount = parseFloat(formData.stake_amount);
  
    if (formData.account_id && stakeAmount > selectedAccountBalance) {
      alert(`Insufficient funds! Available balance: $${selectedAccountBalance.toFixed(2)}`);
      return;
    }
    
    try {
      setSubmitting(true);
      
      const betData = {
        ...formData,
        line_value: formData.line_value ? parseFloat(formData.line_value) : null,
        odds_american: parseInt(formData.odds_american),
        stake_amount: parseFloat(formData.stake_amount),
        account_id: formData.account_id ? parseInt(formData.account_id) : null
      };

      const response = await fetch(`${API_BASE}/bankroll/bets?user_id=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(betData)
      });

      if (response.ok) {
        onBetAdded();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add bet');
      }
    } catch (error) {
      console.error('Error adding bet:', error);
      alert('Failed to add bet');
    } finally {
      setSubmitting(false);
    }
  };

  const submitParlay = async () => {
    const stake = parseFloat(parlayStake);
    const accountId = parseInt(parlayAccount);
    
    // Validation
    if (!parlayAccount) {
      alert('Please select an account');
      return;
    }
    if (!parlayStake || stake <= 0) {
      alert('Please enter a valid stake amount');
      return;
    }
    if (parlayLegs.some(leg => !leg.market_key || !leg.odds_american)) {
      alert('Please complete all leg details');
      return;
    }
    
    const account = accounts.find(acc => acc.account_id === accountId);
    if (account && stake > parseFloat(account.current_balance)) {
      alert(`Insufficient funds! Available balance: $${parseFloat(account.current_balance).toFixed(2)}`);
      return;
    }

    try {
      setSubmitting(true);
      
      const response = await fetch(`${API_BASE}/bankroll/parlays?user_id=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          stake_amount: stake,
          legs: parlayLegs.map(leg => ({
            bet_type: leg.bet_type,
            sport: leg.sport,
            market_key: leg.market_key,
            bet_side: leg.bet_side,
            line_value: leg.line_value ? parseFloat(leg.line_value) : null,
            odds_american: parseInt(leg.odds_american),
            game_id: leg.game_id ? parseInt(leg.game_id) : null,
            player_id: leg.player_id ? parseInt(leg.player_id) : null,
            notes: leg.notes || null
          })),
          notes: parlayNotes
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create parlay');
      }

      onBetAdded();
    } catch (error) {
      console.error('Error creating parlay:', error);
      alert(`Failed to create parlay: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getPositionColor = (position) => {
    const colors = {
      'QB': 'text-purple-400',
      'RB': 'text-emerald-400',
      'WR': 'text-sky-400',
      'TE': 'text-amber-400',
    };
    return colors[position] || 'text-slate-400';
  };

  const isStakeInvalid = formData.account_id && 
                        formData.stake_amount && 
                        parseFloat(formData.stake_amount) > selectedAccountBalance;

  const sportMix = [...new Set(parlayLegs.map(leg => leg.sport))].join(' + ');

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div 
        ref={modalRef}
        className="bg-dark-900 border border-dark-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-900 border-b border-dark-700 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-display font-bold text-white">
              Log New Bet
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tab Selector */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setBetMode('single')}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                betMode === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-800 text-slate-400 hover:text-white'
              }`}
            >
              Single Bet
            </button>
            <button
              type="button"
              onClick={() => setBetMode('parlay')}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                betMode === 'parlay'
                  ? 'bg-purple-600 text-white'
                  : 'bg-dark-800 text-slate-400 hover:text-white'
              }`}
            >
              Parlay
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {betMode === 'single' ? (
            /* ============================================ */
            /* SINGLE BET FORM                              */
            /* ============================================ */
            <div className="space-y-6">
              {/* Account Selection */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Sportsbook Account
                </label>
                <select
                  name="account_id"
                  value={formData.account_id || ''}
                  onChange={handleChange}
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No Account (Manual Entry)</option>
                  {accounts.map((account) => (
                    <option key={account.account_id} value={account.account_id}>
                      {account.bookmaker_name} - ${parseFloat(account.current_balance).toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Bet Type & Sport */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Bet Type
                  </label>
                  <select
                    name="bet_type"
                    value={formData.bet_type}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="player_prop">Player Prop</option>
                    <option value="game_line">Game Line</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Sport
                  </label>
                  <select
                    name="sport"
                    value={formData.sport}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="NFL">NFL</option>
                    <option value="NBA">NBA</option>
                    <option value="MLB">MLB</option>
                    <option value="NHL">NHL</option>
                    <option value="Soccer">Soccer</option>
                  </select>
                </div>
              </div>

              {/* Search Type Toggle */}
              <div className="mb-4">
                <div className="flex gap-2 mb-3">
                  <button
                    type="button"
                    onClick={() => {
                      setSearchType('player');
                      setSelectedTeam(null);
                      setTeamSearch('');
                    }}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      searchType === 'player'
                        ? 'bg-blue-600 text-white'
                        : 'bg-dark-800 text-slate-400 hover:bg-dark-700'
                    }`}
                  >
                    <User className="w-4 h-4 inline mr-2" />
                    Player
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchType('team');
                      setSelectedPlayer(null);
                      setPlayerSearch('');
                    }}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      searchType === 'team'
                        ? 'bg-blue-600 text-white'
                        : 'bg-dark-800 text-slate-400 hover:bg-dark-700'
                    }`}
                  >
                    <TrendingUp className="w-4 h-4 inline mr-2" />
                    Team
                  </button>
                </div>

                {/* Player Search */}
                {searchType === 'player' && (
                  <div ref={searchRef} className="relative">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Search Player
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                      <input
                        type="text"
                        value={playerSearch}
                        onChange={(e) => {
                          setPlayerSearch(e.target.value);
                          searchPlayers(e.target.value);
                          setShowDropdown(true);
                        }}
                        onFocus={() => setShowDropdown(true)}
                        placeholder={`Search ${formData.sport} players...`}
                        className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {searching && (
                        <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500 animate-spin" />
                      )}
                    </div>

                    {/* Player Dropdown */}
                    {showDropdown && playerResults.length > 0 && (
                      <div className="absolute z-50 w-full mt-2 bg-dark-800 border border-dark-700 rounded-lg shadow-xl max-h-64 overflow-y-auto">
                        {playerResults.map((player) => (
                          <button
                            key={player.player_id}
                            type="button"
                            onClick={() => handlePlayerSelect(player)}
                            className="w-full px-4 py-3 text-left hover:bg-dark-700 transition-colors border-b border-dark-700 last:border-0"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-white font-medium">{player.player_name}</p>
                                <p className="text-sm text-slate-400">
                                  {player.position} • {player.team_abbreviation}
                                </p>
                              </div>
                              {player.team_logo_url && (
                                <img 
                                  src={player.team_logo_url} 
                                  alt={player.team_abbreviation}
                                  className="w-8 h-8 object-contain"
                                />
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Selected Player Display */}
                    {selectedPlayer && (
                      <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-white font-medium">{selectedPlayer.player_name}</p>
                            <p className="text-sm text-slate-400">
                              {selectedPlayer.position} • {selectedPlayer.team_abbreviation}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedPlayer(null);
                              setPlayerSearch('');
                              setFormData({ ...formData, player_id: null });
                            }}
                            className="text-slate-400 hover:text-white"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Team Search */}
                {searchType === 'team' && (
                  <div className="relative">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Search Team
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
                      <input
                        type="text"
                        value={teamSearch}
                        onChange={(e) => {
                          setTeamSearch(e.target.value);
                          searchTeams(e.target.value);
                          setShowDropdown(true);
                        }}
                        onFocus={() => setShowDropdown(true)}
                        placeholder={`Search ${formData.sport} teams...`}
                        className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {searching && (
                        <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500 animate-spin" />
                      )}
                    </div>

                    {/* Team Dropdown */}
                    {showDropdown && teamResults.length > 0 && (
                      <div className="absolute z-50 w-full mt-2 bg-dark-800 border border-dark-700 rounded-lg shadow-xl max-h-64 overflow-y-auto">
                        {teamResults.map((team) => (
                          <button
                            key={team.team_id}
                            type="button"
                            onClick={() => handleTeamSelect(team)}
                            className="w-full px-4 py-3 text-left hover:bg-dark-700 transition-colors border-b border-dark-700 last:border-0"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-white font-medium">{team.city} {team.name}</p>
                                <p className="text-sm text-slate-400">{team.abbreviation}</p>
                              </div>
                              {team.logo_url && (
                                <img 
                                  src={team.logo_url} 
                                  alt={team.abbreviation}
                                  className="w-8 h-8 object-contain"
                                />
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Selected Team Display */}
                    {selectedTeam && (
                      <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-white font-medium">{selectedTeam.city} {selectedTeam.name}</p>
                            <p className="text-sm text-slate-400">{selectedTeam.abbreviation}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedTeam(null);
                              setTeamSearch('');
                              setFormData({ ...formData, team_id: null });
                            }}
                            className="text-slate-400 hover:text-white"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Market & Side */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Market
                </label>
                <select
                  value={formData.market_key}
                  onChange={(e) => {
                    const selectedMarket = availableMarkets.find(m => m.key === e.target.value);
                    setFormData({ 
                      ...formData, 
                      market_key: e.target.value,
                      // Clear line if market doesn't require it
                      line_value: selectedMarket?.hasLine ? formData.line_value : ''
                    });
                  }}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select market...</option>
                  {availableMarkets.map((market) => (
                    <option key={market.key} value={market.key}>
                      {market.label} {market.description && `(${market.description})`}
                    </option>
                  ))}
                </select>
                
                {/* Helper text showing what type of bet */}
                <p className="text-xs text-slate-500 mt-1">
                  {selectedPlayer && `${selectedPlayer.position} prop for ${selectedPlayer.player_name}`}
                  {selectedTeam && `Team prop for ${selectedTeam.city} ${selectedTeam.name}`}
                  {!selectedPlayer && !selectedTeam && 'Select a player or team first'}
                </p>
              </div>

              {/* Line Value & Odds */}
              {/* Line Value - only show if market requires it */}
              {marketRequiresLine(formData.market_key) && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Line
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={formData.line_value}
                    onChange={(e) => setFormData({ ...formData, line_value: e.target.value })}
                    placeholder="e.g., 275.5"
                    className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Odds (American)
                  </label>
                  <input
                    type="number"
                    name="odds_american"
                    value={formData.odds_american}
                    onChange={handleChange}
                    required
                    placeholder="e.g., -110 or +150"
                    className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

              {/* Stake Amount */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Stake Amount ($)
                  {formData.account_id && selectedAccountBalance > 0 && (
                    <span className="ml-2 text-xs text-slate-500">
                      Available: ${selectedAccountBalance.toFixed(2)}
                    </span>
                  )}
                </label>
                <input
                  type="number"
                  name="stake_amount"
                  value={formData.stake_amount}
                  onChange={handleChange}
                  required
                  step="0.01"
                  min="0.01"
                  placeholder="e.g., 50.00"
                  className={`w-full px-4 py-2 bg-dark-800 border rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 ${
                    isStakeInvalid
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-dark-700 focus:ring-blue-500'
                  }`}
                />
                {isStakeInvalid && (
                  <p className="mt-1 text-xs text-red-400 flex items-center gap-1">
                    <span>⚠️</span> Exceeds available balance
                  </p>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows={3}
                  placeholder="Add any notes about this bet..."
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>
            </div>
          ) : (
            /* ============================================ */
            /* PARLAY FORM                                  */
            /* ============================================ */
            <div className="space-y-6">
              {/* Parlay Legs */}
              <div className="space-y-3">
                {parlayLegs.map((leg, index) => (
                  <div
                    key={leg.id}
                    className="p-4 bg-dark-800 border border-dark-700 rounded-lg border-l-4 border-l-purple-500"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-white">Leg {index + 1}</h3>
                      {parlayLegs.length > 2 && (
                        <button
                          type="button"
                          onClick={() => removeParlayLeg(index)}
                          className="text-red-500 hover:text-red-400"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {/* Sport */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Sport</label>
                        <select
                          value={leg.sport}
                          onChange={(e) => updateParlayLeg(index, 'sport', e.target.value)}
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="NFL">NFL</option>
                          <option value="NBA">NBA</option>
                          <option value="MLB">MLB</option>
                          <option value="NHL">NHL</option>
                          <option value="Soccer">Soccer</option>
                        </select>
                      </div>

                      {/* Bet Type */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Type</label>
                        <select
                          value={leg.bet_type}
                          onChange={(e) => updateParlayLeg(index, 'bet_type', e.target.value)}
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="player_prop">Player Prop</option>
                          <option value="game_line">Game Line</option>
                        </select>
                      </div>

                      {/* Market */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Market</label>
                        <select
                          value={leg.market_key}
                          onChange={(e) => updateParlayLeg(index, 'market_key', e.target.value)}
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          {leg.sport === 'NFL' && (
                            <>
                              <option value="player_pass_yds">Pass Yards</option>
                              <option value="player_rush_yds">Rush Yards</option>
                              <option value="player_reception_yds">Rec Yards</option>
                              <option value="player_anytime_td">Anytime TD</option>
                              <option value="spread">Spread</option>
                              <option value="totals">Total Points</option>
                            </>
                          )}
                          {leg.sport === 'NBA' && (
                            <>
                              <option value="player_points">Points</option>
                              <option value="player_rebounds">Rebounds</option>
                              <option value="player_assists">Assists</option>
                              <option value="spread">Spread</option>
                              <option value="totals">Total Points</option>
                            </>
                          )}
                        </select>
                      </div>

                      {/* Side */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Side</label>
                        <select
                          value={leg.bet_side}
                          onChange={(e) => updateParlayLeg(index, 'bet_side', e.target.value)}
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          <option value="over">Over</option>
                          <option value="under">Under</option>
                          <option value="home">Home</option>
                          <option value="away">Away</option>
                        </select>
                      </div>

                      {/* Line */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Line</label>
                        <input
                          type="number"
                          step="0.5"
                          value={leg.line_value}
                          onChange={(e) => updateParlayLeg(index, 'line_value', e.target.value)}
                          placeholder="275.5"
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>

                      {/* Odds */}
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Odds</label>
                        <input
                          type="number"
                          value={leg.odds_american}
                          onChange={(e) => updateParlayLeg(index, 'odds_american', e.target.value)}
                          placeholder="-110"
                          className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add Leg Button */}
              <button
                type="button"
                onClick={addParlayLeg}
                disabled={parlayLegs.length >= 15}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-purple-400 hover:bg-dark-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Leg {parlayLegs.length < 15 && `(${15 - parlayLegs.length} remaining)`}
              </button>

              {/* Parlay Summary */}
              <div className="p-4 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-purple-400" />
                  <h3 className="font-semibold text-white">Parlay Summary</h3>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-slate-400">Legs</p>
                    <p className="text-lg font-bold text-white">{parlayLegs.length}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Sport Mix</p>
                    <p className="text-lg font-bold text-white">{sportMix}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Combined Odds</p>
                    <p className="text-lg font-bold text-purple-400">
                      {combinedOdds > 0 ? '+' : ''}{combinedOdds}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Potential Payout</p>
                    <p className="text-lg font-bold text-green-400">
                      ${parlayPayout.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Account</label>
                    <select
                      value={parlayAccount || ''}
                      onChange={(e) => setParlayAccount(e.target.value)}
                      className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="">Select account...</option>
                      {accounts.map(account => (
                        <option key={account.account_id} value={account.account_id}>
                          {account.bookmaker_name} (${parseFloat(account.current_balance).toFixed(2)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Stake ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={parlayStake}
                      onChange={(e) => setParlayStake(e.target.value)}
                      placeholder="100.00"
                      className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>

                <div className="mt-3">
                  <label className="block text-xs text-slate-400 mb-1">Notes</label>
                  <textarea
                    value={parlayNotes}
                    onChange={(e) => setParlayNotes(e.target.value)}
                    placeholder="Parlay notes..."
                    rows={2}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-6">
            <Button
              type="button"
              variant="outline"
              size="lg"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="flex-1"
              disabled={submitting || (betMode === 'single' && isStakeInvalid)}
            >
              {submitting ? 'Adding...' : betMode === 'single' ? 'Add Bet' : `Place Parlay (+${combinedOdds})`}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddBetModal;