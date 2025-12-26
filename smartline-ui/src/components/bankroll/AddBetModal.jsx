import { useState, useEffect, useRef } from 'react';
import { X, Search, User, Loader2 } from 'lucide-react';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const AddBetModal = ({ onClose, onBetAdded, accounts }) => {
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

  const [playerSearch, setPlayerSearch] = useState('');
  const [playerResults, setPlayerResults] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const searchRef = useRef(null);
  const modalRef = useRef(null);

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

  const searchPlayers = async (query) => {
    try {
      setSearching(true);
      const response = await fetch(
        `${API_BASE}/players/search?q=${encodeURIComponent(query)}&limit=8`
      );
      const data = await response.json();
      setPlayerResults(data.results || []);
      setShowDropdown(true);
    } catch (error) {
      console.error('Error searching players:', error);
      setPlayerResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handlePlayerSelect = (player) => {
    setSelectedPlayer(player);
    setFormData({ ...formData, player_id: player.player_id });
    setPlayerSearch(player.full_name);
    setShowDropdown(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      
      // Prepare data
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

  const getPositionColor = (position) => {
    const colors = {
      'QB': 'text-purple-400',
      'RB': 'text-emerald-400',
      'WR': 'text-sky-400',
      'TE': 'text-amber-400',
    };
    return colors[position] || 'text-slate-400';
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div 
        ref={modalRef}
        className="bg-dark-900 border border-dark-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-900 border-b border-dark-700 px-6 py-4 flex items-center justify-between">
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
                  {account.bookmaker_name} - {parseFloat(account.current_balance).toFixed(2)}
                </option>
              ))}
            </select>
          </div>

          {/* Bet Type */}
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
                <option value="parlay">Parlay</option>
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
              </select>
            </div>
          </div>

          {/* Player Search (only for player props) */}
          {formData.bet_type === 'player_prop' && (
            <div ref={searchRef}>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Player
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 pointer-events-none" />
                <input
                  type="text"
                  value={playerSearch}
                  onChange={(e) => setPlayerSearch(e.target.value)}
                  onFocus={() => playerResults.length > 0 && setShowDropdown(true)}
                  placeholder="Search for a player..."
                  className="w-full pl-10 pr-10 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {searching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-400 animate-spin" />
                )}
              </div>

              {/* Selected Player Display */}
              {selectedPlayer && (
                <div className="mt-2 p-3 bg-dark-800 border border-dark-700 rounded-lg flex items-center gap-3">
                  {selectedPlayer.image_url ? (
                    <img
                      src={selectedPlayer.image_url}
                      alt={selectedPlayer.full_name}
                      className="w-10 h-10 rounded-lg object-cover border border-dark-700"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-lg bg-dark-900 border border-dark-700 flex items-center justify-center">
                      <User className="w-5 h-5 text-slate-600" />
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="text-white font-medium">{selectedPlayer.full_name}</p>
                    <p className="text-sm text-slate-400">
                      {selectedPlayer.position} • {selectedPlayer.team_abbrev}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedPlayer(null);
                      setPlayerSearch('');
                      setFormData({ ...formData, player_id: null });
                    }}
                    className="text-slate-500 hover:text-red-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Search Dropdown */}
              {showDropdown && playerResults.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-dark-900 border border-dark-700 rounded-lg shadow-2xl max-h-60 overflow-y-auto">
                  {playerResults.map((player) => (
                    <button
                      key={player.player_id}
                      type="button"
                      onClick={() => handlePlayerSelect(player)}
                      className="w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-800 transition-colors text-left border-b border-dark-700 last:border-0"
                    >
                      {player.image_url ? (
                        <img
                          src={player.image_url}
                          alt={player.full_name}
                          className="w-10 h-10 rounded-lg object-cover border border-dark-700"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-dark-800 border border-dark-700 flex items-center justify-center">
                          <User className="w-5 h-5 text-slate-600" />
                        </div>
                      )}
                      <div className="flex-1">
                        <p className="text-white font-medium">{player.full_name}</p>
                        <div className="flex items-center gap-2 text-sm">
                          {player.position && (
                            <span className={`font-mono ${getPositionColor(player.position)}`}>
                              {player.position}
                            </span>
                          )}
                          {player.team_abbrev && (
                            <>
                              <span className="text-slate-600">•</span>
                              <span className="text-slate-400">{player.team_abbrev}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Market & Side */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Market
              </label>
              <select
                name="market_key"
                value={formData.market_key}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="player_pass_yds">Pass Yards</option>
                <option value="player_pass_tds">Pass TDs</option>
                <option value="player_rush_yds">Rush Yards</option>
                <option value="player_reception_yds">Rec Yards</option>
                <option value="player_anytime_td">Anytime TD</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Side
              </label>
              <select
                name="bet_side"
                value={formData.bet_side}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="over">Over</option>
                <option value="under">Under</option>
              </select>
            </div>
          </div>

          {/* Line Value & Odds */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Line Value
              </label>
              <input
                type="number"
                name="line_value"
                value={formData.line_value}
                onChange={handleChange}
                step="0.5"
                placeholder="e.g., 275.5"
                className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

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
          </div>

          {/* Stake Amount */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Stake Amount ($)
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
              className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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

          {/* Actions */}
          <div className="flex gap-3 pt-4">
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
              disabled={submitting}
            >
              {submitting ? 'Adding...' : 'Add Bet'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddBetModal;
