import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock, TrendingUp, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * ParlayCard Component
 * 
 * Displays parlay details with:
 * - All legs with status indicators
 * - Combined odds and payout
 * - Settlement interface for pending parlays
 * - Visual progress (how many legs won/lost)
 */
export function ParlayCard({ parlay, onUpdate }) {
  const [showSettlement, setShowSettlement] = useState(false);
  const [legResults, setLegResults] = useState({});
  const [settling, setSettling] = useState(false);

  const legs = parlay.legs || [];
  const isPending = parlay.parlay_status === 'pending';
  const isWon = parlay.parlay_status === 'won';
  const isLost = parlay.parlay_status === 'lost';

  function getLegDescription(leg) {
    const parts = [];
    
    if (leg.player_id) {
      parts.push('Player Prop');
    } else if (leg.game_id) {
      parts.push('Game Line');
    }
    
    parts.push(leg.sport);
    parts.push(leg.market_key);
    
    if (leg.bet_side) {
      parts.push(leg.bet_side);
    }
    
    if (leg.line_value) {
      parts.push(leg.line_value);
    }
    
    return parts.join(' • ');
  }

  function getStatusBadge(status) {
    const variants = {
      pending: { color: 'yellow', icon: Clock, text: 'Pending' },
      won: { color: 'green', icon: CheckCircle, text: 'Won' },
      lost: { color: 'red', icon: XCircle, text: 'Lost' },
      push: { color: 'gray', icon: AlertCircle, text: 'Push' }
    };

    const config = variants[status] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.color} className="inline-flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.text}
      </Badge>
    );
  }

  function toggleLegResult(betId, result) {
    setLegResults(prev => ({
      ...prev,
      [betId]: prev[betId] === result ? null : result
    }));
  }

  async function handleSettlement() {
    // Validate all legs have results
    const unsetLegs = legs.filter(leg => !legResults[leg.bet_id]);
    if (unsetLegs.length > 0) {
      alert(`Please set results for all ${legs.length} legs (${unsetLegs.length} remaining)`);
      return;
    }

    setSettling(true);

    try {
      const response = await fetch(
        `${API_BASE}/bankroll/parlays/${parlay.parlay_id}/settle`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(legResults)
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to settle parlay');
      }

      const updated = await response.json();
      onUpdate(updated);
      setShowSettlement(false);
    } catch (error) {
      console.error('Error settling parlay:', error);
      alert(`Failed to settle parlay: ${error.message}`);
    } finally {
      setSettling(false);
    }
  }

  return (
    <Card className="p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold">
              {parlay.total_legs}-Leg Parlay
            </h3>
            {getStatusBadge(parlay.parlay_status)}
          </div>
          <p className="text-sm text-gray-600">
            {parlay.sport_mix} • {parlay.bookmaker_name}
          </p>
          <p className="text-xs text-gray-500">
            {new Date(parlay.placed_at).toLocaleDateString()}
          </p>
        </div>

        <div className="text-right">
          <p className="text-sm text-gray-600">Combined Odds</p>
          <p className="text-2xl font-bold text-blue-600">
            {parlay.combined_odds_american > 0 ? '+' : ''}
            {parlay.combined_odds_american}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-3 mb-4 p-3 bg-gray-50 rounded">
        <div className="text-center">
          <p className="text-xs text-gray-600">Stake</p>
          <p className="font-bold">${parlay.stake_amount.toFixed(2)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">To Win</p>
          <p className="font-bold text-green-600">
            ${(parlay.potential_payout - parlay.stake_amount).toFixed(2)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">Payout</p>
          <p className="font-bold">${parlay.potential_payout.toFixed(2)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">Result</p>
          <p className={`font-bold ${
            (parlay.profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {(parlay.profit_loss || 0) >= 0 ? '+' : ''}
            ${(parlay.profit_loss || 0).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Leg Progress */}
      {isPending && (
        <div className="mb-4 p-3 bg-blue-50 rounded">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Leg Progress</span>
            <span className="text-sm">
              {parlay.legs_won}/{parlay.total_legs} Won
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(parlay.legs_won / parlay.total_legs) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-600 mt-1">
            <span>{parlay.legs_won} Won</span>
            <span>{parlay.legs_lost} Lost</span>
            <span>{parlay.legs_pending} Pending</span>
          </div>
        </div>
      )}

      {/* Legs List */}
      <div className="space-y-2 mb-4">
        <h4 className="font-semibold text-sm">Legs:</h4>
        {legs.map((leg, index) => (
          <div
            key={leg.bet_id}
            className={`p-3 rounded border-l-4 ${
              leg.status === 'won' ? 'border-green-500 bg-green-50' :
              leg.status === 'lost' ? 'border-red-500 bg-red-50' :
              'border-gray-300 bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">Leg {index + 1}</span>
                  {getStatusBadge(leg.status)}
                </div>
                <p className="text-sm text-gray-700">
                  {getLegDescription(leg)}
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  Odds: {leg.odds_american > 0 ? '+' : ''}{leg.odds_american}
                </p>
              </div>

              {/* Settlement Controls (when in settlement mode) */}
              {showSettlement && (
                <div className="flex gap-1 ml-2">
                  <button
                    onClick={() => toggleLegResult(leg.bet_id, 'won')}
                    className={`px-3 py-1 rounded text-xs font-medium ${
                      legResults[leg.bet_id] === 'won'
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Won
                  </button>
                  <button
                    onClick={() => toggleLegResult(leg.bet_id, 'lost')}
                    className={`px-3 py-1 rounded text-xs font-medium ${
                      legResults[leg.bet_id] === 'lost'
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Lost
                  </button>
                  <button
                    onClick={() => toggleLegResult(leg.bet_id, 'push')}
                    className={`px-3 py-1 rounded text-xs font-medium ${
                      legResults[leg.bet_id] === 'push'
                        ? 'bg-gray-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Push
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Notes */}
      {parlay.notes && (
        <div className="mb-4 p-3 bg-yellow-50 rounded">
          <p className="text-sm text-gray-700">{parlay.notes}</p>
        </div>
      )}

      {/* Actions */}
      {isPending && (
        <div className="flex gap-2">
          {!showSettlement ? (
            <Button
              variant="primary"
              onClick={() => {
                setShowSettlement(true);
                // Initialize with current statuses
                const initial = {};
                legs.forEach(leg => {
                  if (leg.status !== 'pending') {
                    initial[leg.bet_id] = leg.status;
                  }
                });
                setLegResults(initial);
              }}
              className="flex-1"
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Settle Parlay
            </Button>
          ) : (
            <>
              <Button
                variant="ghost"
                onClick={() => setShowSettlement(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSettlement}
                disabled={settling || legs.some(leg => !legResults[leg.bet_id])}
                className="flex-1"
              >
                {settling ? 'Settling...' : 'Confirm Settlement'}
              </Button>
            </>
          )}
        </div>
      )}

      {/* Result Message */}
      {isWon && (
        <div className="p-3 bg-green-50 border border-green-200 rounded">
          <p className="text-green-800 font-semibold text-center">
            🎉 Parlay Won! +${parlay.profit_loss.toFixed(2)}
          </p>
        </div>
      )}

      {isLost && (
        <div className="p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-red-800 font-semibold text-center">
            Parlay Lost - ${Math.abs(parlay.profit_loss).toFixed(2)}
          </p>
        </div>
      )}
    </Card>
  );
}
