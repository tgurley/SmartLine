import { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, MinusCircle, Edit, Trash2, DollarSign } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const RecentBets = ({ onBetUpdated }) => {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [settlingBetId, setSettlingBetId] = useState(null);

  useEffect(() => {
    fetchBets();
  }, []);

  const fetchBets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/bankroll/bets?user_id=1&limit=10&page=1`);
      const data = await response.json();
      setBets(data.bets || []);
    } catch (error) {
      console.error('Error fetching bets:', error);
      setBets([]);
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
        fetchBets();
        if (onBetUpdated) onBetUpdated();
      } else {
        console.error('Failed to settle bet');
      }
    } catch (error) {
      console.error('Error settling bet:', error);
    } finally {
      setSettlingBetId(null);
    }
  };

  const deleteBet = async (betId) => {
    if (!confirm('Are you sure you want to delete this bet?')) return;

    try {
      const response = await fetch(`${API_BASE}/bankroll/bets/${betId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchBets();
        if (onBetUpdated) onBetUpdated();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to delete bet');
      }
    } catch (error) {
      console.error('Error deleting bet:', error);
      alert('Failed to delete bet');
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
              Your latest {bets.length} wagers
            </Card.Description>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchBets}>
            Refresh
          </Button>
        </div>
      </Card.Header>
      <Card.Content>
        {bets.length === 0 ? (
          <div className="text-center py-12">
            <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">No bets logged yet</p>
            <p className="text-sm text-slate-500">Click "Log Bet" to add your first wager</p>
          </div>
        ) : (
          <div className="space-y-3">
            {bets.map((bet, index) => (
              <div
                key={bet.bet_id}
                className="group relative bg-dark-800 rounded-lg p-4 hover:bg-dark-700 transition-all border border-dark-700 hover:border-dark-600 animate-slide-up"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Left: Bet Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      {/* Player/Team Name */}
                      <h3 className="text-white font-semibold truncate">
                        {bet.player_name || 'Game Bet'}
                      </h3>
                      
                      {/* Position Badge */}
                      {bet.player_position && (
                        <Badge variant="default" size="sm">
                          {bet.player_position}
                        </Badge>
                      )}
                      
                      {/* Bookmaker */}
                      {bet.bookmaker_name && (
                        <span className="text-xs text-slate-500">
                          • {bet.bookmaker_name}
                        </span>
                      )}
                    </div>

                    {/* Bet Line */}
                    <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400 mb-2">
                      <span className="font-medium">
                        {formatMarketKey(bet.market_key)}
                        {bet.bet_side && ` ${bet.bet_side.toUpperCase()}`}
                        {bet.line_value && ` ${bet.line_value}`}
                      </span>
                      <span>@</span>
                      <span className="font-mono text-slate-300">
                        {formatOdds(bet.odds_american)}
                      </span>
                    </div>

                    {/* Stake & Date */}
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span className="font-mono font-medium">
                        Stake: {formatCurrency(bet.stake_amount)}
                      </span>
                      <span>•</span>
                      <span>
                        {new Date(bet.placed_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>

                    {/* Notes */}
                    {bet.notes && (
                      <p className="text-xs text-slate-500 mt-2 italic">
                        "{bet.notes}"
                      </p>
                    )}
                  </div>

                  {/* Right: Status & Actions */}
                  <div className="flex flex-col items-end gap-2">
                    {/* Status Badge */}
                    {getStatusBadge(bet.status)}

                    {/* Profit/Loss */}
                    {bet.profit_loss !== null && (
                      <div className="text-right">
                        {getProfitLossDisplay(bet.profit_loss)}
                      </div>
                    )}

                    {/* Quick Settle Actions (for pending bets) */}
                    {bet.status === 'pending' && (
                      <div className="flex gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => settleBet(bet.bet_id, 'won')}
                          disabled={settlingBetId === bet.bet_id}
                          className="px-2 py-1 text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/30 transition-colors disabled:opacity-50"
                          title="Mark as Won"
                        >
                          Win
                        </button>
                        <button
                          onClick={() => settleBet(bet.bet_id, 'lost')}
                          disabled={settlingBetId === bet.bet_id}
                          className="px-2 py-1 text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded border border-red-500/30 transition-colors disabled:opacity-50"
                          title="Mark as Lost"
                        >
                          Loss
                        </button>
                        <button
                          onClick={() => settleBet(bet.bet_id, 'push')}
                          disabled={settlingBetId === bet.bet_id}
                          className="px-2 py-1 text-xs bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 rounded border border-slate-500/30 transition-colors disabled:opacity-50"
                          title="Mark as Push"
                        >
                          Push
                        </button>
                      </div>
                    )}

                    {/* Delete button (for pending bets) */}
                    {bet.status === 'pending' && (
                      <button
                        onClick={() => deleteBet(bet.bet_id)}
                        className="p-1 text-slate-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete Bet"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card.Content>
      {bets.length > 0 && (
        <Card.Footer>
          <Button variant="ghost" size="sm">
            View all bets
          </Button>
          <span className="text-sm text-slate-500">
            {bets.length} recent
          </span>
        </Card.Footer>
      )}
    </Card>
  );
};

export default RecentBets;
