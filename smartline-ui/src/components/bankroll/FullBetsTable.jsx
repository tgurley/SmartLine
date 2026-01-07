import { useState, useEffect } from 'react';
import { Filter, Search, ChevronLeft, ChevronRight, Edit, Trash2, CheckCircle, MinusCircle, XCircle, Clock, Download, Layers, ChevronDown, ChevronUp } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const FullBetsTable = ({ onBetUpdated, onEditBet }) => {
  const [bets, setBets] = useState([]);
  const [parlays, setParlays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0
  });

  // Filters
  const [filters, setFilters] = useState({
    type: 'all', // 'all', 'single', 'parlay'
    status: '',
    account_id: '',
    bet_type: '',
    market_key: '',
    start_date: '',
    end_date: '',
    search: ''
  });

  const [accounts, setAccounts] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedParlays, setExpandedParlays] = useState({});
  const [settlingBetId, setSettlingBetId] = useState(null);
  const [settlingParlayId, setSettlingParlayId] = useState(null);
  const [legResults, setLegResults] = useState({});

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    fetchBetsAndParlays();
  }, [pagination.page, pagination.limit, filters]);

  const fetchAccounts = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/accounts?user_id=1`);
      const data = await response.json();
      setAccounts(data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const fetchBetsAndParlays = async () => {
    try {
      setLoading(true);
      
      // Build query params for single bets (exclude parlay legs!)
      const params = new URLSearchParams({
        user_id: '1',
        page: pagination.page.toString(),
        limit: pagination.limit.toString(),
        parlay_id: 'null' // CRITICAL: Only fetch single bets, not parlay legs
      });

      if (filters.status) params.append('status', filters.status);
      if (filters.account_id) params.append('account_id', filters.account_id);
      if (filters.bet_type) params.append('bet_type', filters.bet_type);
      if (filters.market_key) params.append('market_key', filters.market_key);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);

      // Fetch based on filter type
      if (filters.type === 'all' || filters.type === 'single') {
        const betsResponse = await fetch(`${API_BASE}/bankroll/bets?${params}`);
        const betsData = await betsResponse.json();
        setBets(betsData.bets || []);
      } else {
        setBets([]);
      }

      if (filters.type === 'all' || filters.type === 'parlay') {
        // Build params for parlays
        const parlayParams = new URLSearchParams({
          user_id: '1',
          limit: pagination.limit.toString()
        });
        
        if (filters.status) parlayParams.append('status', filters.status);
        if (filters.account_id) parlayParams.append('account_id', filters.account_id);

        const parlaysResponse = await fetch(`${API_BASE}/bankroll/parlays?${parlayParams}`);
        const parlaysData = await parlaysResponse.json();
        setParlays(Array.isArray(parlaysData) ? parlaysData : []);
      } else {
        setParlays([]);
      }

    } catch (error) {
      console.error('Error fetching bets/parlays:', error);
      setBets([]);
      setParlays([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
    setPagination({ ...pagination, page: 1 });
  };

  const clearFilters = () => {
    setFilters({
      type: 'all',
      status: '',
      account_id: '',
      bet_type: '',
      market_key: '',
      start_date: '',
      end_date: '',
      search: ''
    });
  };

  const settleBet = async (betId, status) => {
    try {
      setSettlingBetId(betId);
      const response = await fetch(`${API_BASE}/bankroll/bets/${betId}/settle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        fetchBetsAndParlays();
        if (onBetUpdated) onBetUpdated();
      }
    } catch (error) {
      console.error('Error settling bet:', error);
    } finally {
      setSettlingBetId(null);
    }
  };

  const deleteBet = async (betId) => {
    if (!confirm('Delete this bet?')) return;

    try {
      await fetch(`${API_BASE}/bankroll/bets/${betId}`, { method: 'DELETE' });
      fetchBetsAndParlays();
      if (onBetUpdated) onBetUpdated();
    } catch (error) {
      console.error('Error deleting bet:', error);
    }
  };

  const toggleLegResult = (parlayId, betId, result) => {
    setLegResults(prev => ({
      ...prev,
      [parlayId]: {
        ...prev[parlayId],
        [betId]: prev[parlayId]?.[betId] === result ? null : result
      }
    }));
  };

  const settleParlay = async (parlayId) => {
    const results = legResults[parlayId];
    if (!results) {
      alert('Please set results for all legs');
      return;
    }

    const parlay = parlays.find(p => p.parlay_id === parlayId);
    if (Object.keys(results).length !== parlay.total_legs) {
      alert(`Please set results for all ${parlay.total_legs} legs`);
      return;
    }

    try {
      setSettlingParlayId(parlayId);
      const response = await fetch(`${API_BASE}/bankroll/parlays/${parlayId}/settle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(results)
      });

      if (response.ok) {
        setLegResults(prev => {
          const newResults = { ...prev };
          delete newResults[parlayId];
          return newResults;
        });
        fetchBetsAndParlays();
        if (onBetUpdated) onBetUpdated();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to settle parlay');
      }
    } catch (error) {
      console.error('Error settling parlay:', error);
    } finally {
      setSettlingParlayId(null);
    }
  };

  const deleteParlay = async (parlayId) => {
    if (!confirm('Delete this parlay?')) return;

    try {
      await fetch(`${API_BASE}/bankroll/parlays/${parlayId}`, { method: 'DELETE' });
      fetchBetsAndParlays();
      if (onBetUpdated) onBetUpdated();
    } catch (error) {
      console.error('Error deleting parlay:', error);
    }
  };

  const toggleParlayExpand = (parlayId) => {
    setExpandedParlays(prev => ({
      ...prev,
      [parlayId]: !prev[parlayId]
    }));
  };

  const exportToCSV = () => {
    // Implementation for CSV export
    console.log('Export to CSV');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(parseFloat(amount));
  };

  const formatOdds = (odds) => {
    return odds > 0 ? `+${odds}` : odds.toString();
  };

  const formatMarketKey = (key) => {
    const names = {
      'player_pass_yds': 'Pass Yds',
      'player_pass_tds': 'Pass TDs',
      'player_rush_yds': 'Rush Yds',
      'player_reception_yds': 'Rec Yds',
      'player_anytime_td': 'Anytime TD',
      'spread': 'Spread',
      'total': 'Total'
    };
    return names[key] || key;
  };

  const getStatusBadge = (status) => {
    const variants = {
      'pending': { variant: 'default', icon: Clock, text: 'Pending' },
      'won': { variant: 'success', icon: CheckCircle, text: 'Won' },
      'lost': { variant: 'error', icon: XCircle, text: 'Lost' },
      'push': { variant: 'warning', icon: MinusCircle, text: 'Push' }
    };

    const config = variants[status] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} size="sm">
        <Icon className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  const getProfitLossDisplay = (profitLoss) => {
    if (profitLoss === null || profitLoss === undefined) return null;
    
    const num = parseFloat(profitLoss);
    const isProfit = num > 0;
    const isLoss = num < 0;
    
    return (
      <span className={`font-mono font-bold ${
        isProfit ? 'text-emerald-400' : isLoss ? 'text-red-400' : 'text-slate-400'
      }`}>
        {isProfit ? '+' : ''}{formatCurrency(num)}
      </span>
    );
  };

  // Combine and sort all wagers
  const allWagers = [
    ...bets.map(bet => ({ ...bet, type: 'single' })),
    ...parlays.map(parlay => ({ ...parlay, type: 'parlay', placed_at: parlay.placed_at, status: parlay.parlay_status }))
  ].sort((a, b) => new Date(b.placed_at) - new Date(a.placed_at));

  const totalCount = bets.length + parlays.length;

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 w-full">
          <div>
            <Card.Title>All Bets & Parlays</Card.Title>
            <Card.Description>
              {totalCount} total wagers • {bets.length} singles, {parlays.length} parlays
            </Card.Description>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportToCSV}
              disabled={allWagers.length === 0}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </Card.Header>

      {/* Filters */}
      {showFilters && (
        <div className="px-6 pb-4 border-b border-dark-700">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Type Filter */}
            <select
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="single">Single Bets</option>
              <option value="parlay">Parlays</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="won">Won</option>
              <option value="lost">Lost</option>
              <option value="push">Push</option>
            </select>

            {/* Account Filter */}
            <select
              value={filters.account_id}
              onChange={(e) => handleFilterChange('account_id', e.target.value)}
              className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Sportsbooks</option>
              {accounts.map((account) => (
                <option key={account.account_id} value={account.account_id}>
                  {account.bookmaker_name}
                </option>
              ))}
            </select>

            {/* Date Range */}
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              placeholder="Start Date"
              className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end mt-3">
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </div>
      )}

      <Card.Content>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-dark-800 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : allWagers.length === 0 ? (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No bets found</p>
            <p className="text-sm text-slate-500 mt-1">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="space-y-3">
            {allWagers.map((wager) => (
              wager.type === 'single' ? (
                // SINGLE BET ROW
                <div
                  key={`bet-${wager.bet_id}`}
                  className="group bg-dark-800 rounded-lg p-4 hover:bg-dark-700 transition-all border border-dark-700"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-6 gap-4">
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Date</p>
                        <p className="text-sm text-white">
                          {new Date(wager.placed_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric'
                          })}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500 mb-1">Player/Game</p>
                        <p className="text-sm text-white font-medium truncate">
                          {wager.player_name || 'Game Bet'}
                        </p>
                        <p className="text-xs text-slate-500">{wager.bookmaker_name}</p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500 mb-1">Market</p>
                        <p className="text-sm text-white">
                          {formatMarketKey(wager.market_key)} {wager.bet_side?.toUpperCase()}
                        </p>
                        <p className="text-xs text-slate-500">{wager.line_value}</p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500 mb-1">Odds</p>
                        <p className="text-sm font-mono text-white">{formatOdds(wager.odds_american)}</p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500 mb-1">Stake</p>
                        <p className="text-sm font-mono text-white">{formatCurrency(wager.stake_amount)}</p>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500 mb-1">Status & P/L</p>
                        {getStatusBadge(wager.status)}
                        {wager.profit_loss !== null && (
                          <div className="mt-1">
                            {getProfitLossDisplay(wager.profit_loss)}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      {wager.status === 'pending' && (
                        <>
                          <div className="flex gap-1">
                            <button
                              onClick={() => settleBet(wager.bet_id, 'won')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/30"
                            >
                              W
                            </button>
                            <button
                              onClick={() => settleBet(wager.bet_id, 'lost')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded border border-red-500/30"
                            >
                              L
                            </button>
                            <button
                              onClick={() => settleBet(wager.bet_id, 'push')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 rounded border border-slate-500/30"
                            >
                              P
                            </button>
                          </div>
                          <button
                            onClick={() => deleteBet(wager.bet_id)}
                            className="px-2 py-1 text-xs bg-dark-700 text-slate-400 hover:bg-red-500/10 hover:text-red-400 rounded border border-dark-600"
                          >
                            <Trash2 className="w-3 h-3 mx-auto" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                // PARLAY ROW
                <div
                  key={`parlay-${wager.parlay_id}`}
                  className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-lg border border-purple-500/30"
                >
                  {/* Parlay Header */}
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 grid grid-cols-1 md:grid-cols-6 gap-4">
                        <div>
                          <p className="text-xs text-slate-500 mb-1">Date</p>
                          <p className="text-sm text-white">
                            {new Date(wager.placed_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric'
                            })}
                          </p>
                        </div>

                        <div className="md:col-span-2">
                          <p className="text-xs text-slate-500 mb-1">Type</p>
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-purple-400" />
                            <p className="text-sm text-white font-medium">
                              {wager.total_legs}-Leg Parlay
                            </p>
                            <Badge variant="default" size="sm" className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                              {wager.sport_mix}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500">{wager.bookmaker_name}</p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-500 mb-1">Odds</p>
                          <p className="text-sm font-mono text-purple-300 font-bold">
                            {formatOdds(wager.combined_odds_american)}
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-500 mb-1">Stake</p>
                          <p className="text-sm font-mono text-white">{formatCurrency(wager.stake_amount)}</p>
                          <p className="text-xs text-green-400">
                            Win: {formatCurrency(wager.potential_payout - wager.stake_amount)}
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-500 mb-1">Status & P/L</p>
                          {getStatusBadge(wager.status)}
                          {wager.profit_loss !== null && (
                            <div className="mt-1">
                              {getProfitLossDisplay(wager.profit_loss)}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Expand Button & Actions */}
                      <div className="flex flex-col gap-2">
                        <button
                          onClick={() => toggleParlayExpand(wager.parlay_id)}
                          className="p-2 text-purple-400 hover:text-purple-300 transition-colors"
                        >
                          {expandedParlays[wager.parlay_id] ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>

                        {wager.status === 'pending' && (
                          <button
                            onClick={() => deleteParlay(wager.parlay_id)}
                            className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Legs */}
                  {expandedParlays[wager.parlay_id] && (
                    <div className="px-4 pb-4 space-y-2 border-t border-purple-500/20">
                      <p className="text-xs text-purple-300 font-medium mt-3 mb-2">PARLAY LEGS:</p>
                      {wager.legs && wager.legs.map((leg, idx) => (
                        <div
                          key={leg.bet_id}
                          className={`p-3 rounded text-sm border ${
                            leg.status === 'won' ? 'bg-green-500/10 border-green-500/30' :
                            leg.status === 'lost' ? 'bg-red-500/10 border-red-500/30' :
                            leg.status === 'push' ? 'bg-slate-500/10 border-slate-500/30' :
                            'bg-dark-800/50 border-dark-700'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex-1">
                              <span className="text-slate-400">Leg {idx + 1}:</span>
                              <span className="text-white ml-2">
                                {leg.sport} • {formatMarketKey(leg.market_key)} {leg.bet_side?.toUpperCase()} {leg.line_value}
                              </span>
                              <span className="text-slate-400 ml-2">@ {formatOdds(leg.odds_american)}</span>
                            </div>

                            {wager.status === 'pending' && (
                              <div className="flex gap-1">
                                <button
                                  onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'won')}
                                  className={`px-3 py-1 rounded text-xs transition-colors ${
                                    legResults[wager.parlay_id]?.[leg.bet_id] === 'won'
                                      ? 'bg-green-600 text-white'
                                      : 'bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/30'
                                  }`}
                                >
                                  Won
                                </button>
                                <button
                                  onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'lost')}
                                  className={`px-3 py-1 rounded text-xs transition-colors ${
                                    legResults[wager.parlay_id]?.[leg.bet_id] === 'lost'
                                      ? 'bg-red-600 text-white'
                                      : 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/30'
                                  }`}
                                >
                                  Lost
                                </button>
                                <button
                                  onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'push')}
                                  className={`px-3 py-1 rounded text-xs transition-colors ${
                                    legResults[wager.parlay_id]?.[leg.bet_id] === 'push'
                                      ? 'bg-slate-600 text-white'
                                      : 'bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 border border-slate-500/30'
                                  }`}
                                >
                                  Push
                                </button>
                              </div>
                            )}

                            {leg.status && leg.status !== 'pending' && (
                              <Badge variant={
                                leg.status === 'won' ? 'success' :
                                leg.status === 'lost' ? 'error' : 'warning'
                              } size="sm">
                                {leg.status.toUpperCase()}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}

                      {/* Settle Button */}
                      {wager.status === 'pending' && (
                        <button
                          onClick={() => settleParlay(wager.parlay_id)}
                          disabled={settlingParlayId === wager.parlay_id}
                          className="w-full mt-3 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-medium transition-colors disabled:opacity-50"
                        >
                          {settlingParlayId === wager.parlay_id ? 'Settling...' : 'Settle Parlay'}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )
            ))}
          </div>
        )}
      </Card.Content>

      {/* Pagination */}
      {allWagers.length > 0 && (
        <Card.Footer>
          <div className="flex items-center justify-between w-full">
            <p className="text-sm text-slate-500">
              Showing {allWagers.length} wagers
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                disabled={pagination.page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                disabled={pagination.page === pagination.pages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card.Footer>
      )}
    </Card>
  );
};

export default FullBetsTable;
