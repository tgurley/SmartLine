import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, CheckCircle, XCircle, MinusCircle, Edit, Trash2, DollarSign, List, Layers } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const RecentBets = ({ onBetUpdated, onEditBet }) => {
  const [bets, setBets] = useState([]);
  const [parlays, setParlays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [settlingBetId, setSettlingBetId] = useState(null);
  const [settlingParlayId, setSettlingParlayId] = useState(null);
  const [legResults, setLegResults] = useState({});

  useEffect(() => {
    fetchBetsAndParlays();
  }, []);

  const fetchBetsAndParlays = async () => {
    try {
      setLoading(true);
      
      // Fetch single bets ONLY (exclude parlay legs with parlay_id filter)
      const betsResponse = await fetch(`${API_BASE}/bankroll/bets?user_id=1&limit=5&page=1&parlay_id=null`);
      const betsData = await betsResponse.json();
      
      // Fetch parlays
      const parlaysResponse = await fetch(`${API_BASE}/bankroll/parlays?user_id=1&limit=5`);
      const parlaysData = await parlaysResponse.json();
      
      // Handle different response formats
      setBets(betsData.bets || []);
      setParlays(Array.isArray(parlaysData) ? parlaysData : []);
    } catch (error) {
      console.error('Error fetching bets/parlays:', error);
      setBets([]);
      setParlays([]);
    } finally {
      setLoading(false);
    }
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
      alert('Failed to settle parlay');
    } finally {
      setSettlingParlayId(null);
    }
  };

  const deleteBet = async (betId) => {
    if (!confirm('Are you sure you want to delete this bet?')) return;

    try {
      const response = await fetch(`${API_BASE}/bankroll/bets/${betId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchBetsAndParlays();
        if (onBetUpdated) onBetUpdated();
      }
    } catch (error) {
      console.error('Error deleting bet:', error);
    }
  };

  const deleteParlay = async (parlayId) => {
    if (!confirm('Are you sure you want to delete this parlay?')) return;

    try {
      const response = await fetch(`${API_BASE}/bankroll/parlays/${parlayId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchBetsAndParlays();
        if (onBetUpdated) onBetUpdated();
      }
    } catch (error) {
      console.error('Error deleting parlay:', error);
    }
  };

  const formatCurrency = (amount) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
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
      'push': { variant: 'warning', icon: MinusCircle, text: 'Push' },
      'cancelled': { variant: 'default', icon: MinusCircle, text: 'Cancelled' }
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
    if (!profitLoss) return null;
    
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

  // Combine bets and parlays, sort by date
  const allWagers = [
    ...bets.map(bet => ({ ...bet, type: 'single' })),
    ...parlays.map(parlay => ({ ...parlay, type: 'parlay', placed_at: parlay.placed_at }))
  ].sort((a, b) => new Date(b.placed_at) - new Date(a.placed_at)).slice(0, 10);

  if (loading) {
    return (
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Recent Bets</Card.Title>
          <Card.Description>Loading...</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-20 bg-dark-800 rounded-lg animate-pulse"></div>
            ))}
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex items-center justify-between w-full">
          <div>
            <Card.Title>Recent Bets</Card.Title>
            <Card.Description>
              Your latest {allWagers.length} wagers
            </Card.Description>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchBetsAndParlays}>
            Refresh
          </Button>
        </div>
      </Card.Header>
      <Card.Content>
        {allWagers.length === 0 ? (
          <div className="text-center py-12">
            <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">No bets logged yet</p>
            <p className="text-sm text-slate-500">Click "Log Bet" to add your first wager</p>
          </div>
        ) : (
          <div className="space-y-3">
            {allWagers.map((wager, index) => (
              wager.type === 'single' ? (
                // SINGLE BET CARD
                <div
                  key={`bet-${wager.bet_id}`}
                  className="group relative bg-dark-800 rounded-lg p-4 hover:bg-dark-700 transition-all border border-dark-700 hover:border-dark-600 animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-white font-semibold truncate">
                          {wager.full_name || 'Game Bet'}
                        </h3>
                        {wager.player_position && (
                          <Badge variant="default" size="sm">{wager.player_position}</Badge>
                        )}
                        {wager.bookmaker_name && (
                          <span className="text-xs text-slate-500">• {wager.bookmaker_name}</span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400 mb-2">
                        <span className="font-medium">
                          {formatMarketKey(wager.market_key)}
                          {wager.bet_side && ` ${wager.bet_side.toUpperCase()}`}
                          {wager.line_value && ` ${wager.line_value}`}
                        </span>
                        <span>@</span>
                        <span className="font-mono text-slate-300">
                          {formatOdds(wager.odds_american)}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span className="font-mono font-medium">
                          Stake: {formatCurrency(wager.stake_amount)}
                        </span>
                        <span>•</span>
                        <span>
                          {new Date(wager.placed_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>

                      {wager.notes && (
                        <p className="text-xs text-slate-500 mt-2 italic">"{wager.notes}"</p>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      {getStatusBadge(wager.status)}
                      {wager.profit_loss !== null && (
                        <div className="text-right">
                          {getProfitLossDisplay(wager.profit_loss)}
                        </div>
                      )}

                      {wager.status === 'pending' && (
                        <div className="flex flex-col gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <div className="flex gap-1">
                            <button
                              onClick={() => settleBet(wager.bet_id, 'won')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/30 transition-colors"
                            >
                              Win
                            </button>
                            <button
                              onClick={() => settleBet(wager.bet_id, 'lost')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded border border-red-500/30 transition-colors"
                            >
                              Loss
                            </button>
                            <button
                              onClick={() => settleBet(wager.bet_id, 'push')}
                              disabled={settlingBetId === wager.bet_id}
                              className="px-2 py-1 text-xs bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 rounded border border-slate-500/30 transition-colors"
                            >
                              Push
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                // PARLAY CARD
                <div
                  key={`parlay-${wager.parlay_id}`}
                  className="group relative bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-lg p-4 hover:from-purple-900/30 hover:to-blue-900/30 transition-all border border-purple-500/30 hover:border-purple-500/50 animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Layers className="w-4 h-4 text-purple-400" />
                        <h3 className="text-white font-semibold">
                          {wager.total_legs}-Leg Parlay
                        </h3>
                        <Badge variant="default" size="sm" className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                          {wager.sport_mix}
                        </Badge>
                        {wager.bookmaker_name && (
                          <span className="text-xs text-slate-500">• {wager.bookmaker_name}</span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-sm text-slate-400 mb-2">
                        <span className="font-mono text-purple-300 font-bold">
                          {formatOdds(wager.combined_odds_american)}
                        </span>
                        <span>•</span>
                        <span className="font-mono">Stake: {formatCurrency(wager.stake_amount)}</span>
                        <span>•</span>
                        <span className="text-green-400">To Win: {formatCurrency(wager.potential_payout - wager.stake_amount)}</span>
                      </div>

                      <div className="text-xs text-slate-500">
                        {new Date(wager.placed_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      {getStatusBadge(wager.parlay_status)}
                      {wager.profit_loss !== null && (
                        <div className="text-right">
                          {getProfitLossDisplay(wager.profit_loss)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Parlay Legs */}
                  <div className="space-y-2 mb-3">
                    {wager.legs && wager.legs.map((leg, legIdx) => (
                      <div
                        key={leg.bet_id}
                        className={`p-2 rounded text-xs border ${
                          leg.status === 'won' ? 'bg-green-500/10 border-green-500/30' :
                          leg.status === 'lost' ? 'bg-red-500/10 border-red-500/30' :
                          leg.status === 'push' ? 'bg-slate-500/10 border-slate-500/30' :
                          'bg-dark-800/50 border-dark-700'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex-1">
                            <span className="text-slate-400">Leg {legIdx + 1}:</span>
                            <span className="text-white ml-2">
                              {leg.sport} • {formatMarketKey(leg.market_key)} {leg.bet_side?.toUpperCase()} {leg.line_value}
                            </span>
                            <span className="text-slate-400 ml-2">@ {formatOdds(leg.odds_american)}</span>
                          </div>

                          {wager.parlay_status === 'pending' && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'won')}
                                className={`px-2 py-1 rounded text-xs transition-colors ${
                                  legResults[wager.parlay_id]?.[leg.bet_id] === 'won'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/30'
                                }`}
                              >
                                W
                              </button>
                              <button
                                onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'lost')}
                                className={`px-2 py-1 rounded text-xs transition-colors ${
                                  legResults[wager.parlay_id]?.[leg.bet_id] === 'lost'
                                    ? 'bg-red-600 text-white'
                                    : 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/30'
                                }`}
                              >
                                L
                              </button>
                              <button
                                onClick={() => toggleLegResult(wager.parlay_id, leg.bet_id, 'push')}
                                className={`px-2 py-1 rounded text-xs transition-colors ${
                                  legResults[wager.parlay_id]?.[leg.bet_id] === 'push'
                                    ? 'bg-slate-600 text-white'
                                    : 'bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 border border-slate-500/30'
                                }`}
                              >
                                P
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
                  </div>

                  {/* Settle/Delete Actions */}
                  {wager.parlay_status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => settleParlay(wager.parlay_id)}
                        disabled={settlingParlayId === wager.parlay_id}
                        className="flex-1 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-medium text-sm transition-colors disabled:opacity-50"
                      >
                        {settlingParlayId === wager.parlay_id ? 'Settling...' : 'Settle Parlay'}
                      </button>
                      <button
                        onClick={() => deleteParlay(wager.parlay_id)}
                        className="px-3 py-2 bg-dark-700 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              )
            ))}
          </div>
        )}
      </Card.Content>
      {allWagers.length > 0 && (
        <Card.Footer>
          <Link to="/bankroll/bets">
            <Button variant="outline" size="md" className="w-full">
              <List className="w-4 h-4 mr-2" />
              View All Bets
            </Button>
          </Link>
        </Card.Footer>
      )}
    </Card>
  );
};

export default RecentBets;
