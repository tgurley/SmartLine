import React, { useState, useEffect } from 'react';
import { Plus, X, TrendingUp } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * ParlayBuilder Component
 * 
 * Allows users to build multi-leg parlay bets with:
 * - Dynamic leg addition/removal
 * - Multi-sport support
 * - Real-time odds calculation
 * - Automatic payout calculation
 */
export function ParlayBuilder({ accounts, onSave, onCancel }) {
  const [legs, setLegs] = useState([createEmptyLeg(1)]);
  const [stake, setStake] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Calculate combined odds whenever legs change
  const combinedOdds = calculateParlayOdds(legs);
  const potentialPayout = stake ? calculatePayout(parseFloat(stake), combinedOdds) : 0;

  function createEmptyLeg(number) {
    return {
      number,
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

  function addLeg() {
    if (legs.length >= 15) {
      alert('Maximum 15 legs allowed per parlay');
      return;
    }
    setLegs([...legs, createEmptyLeg(legs.length + 1)]);
  }

  function removeLeg(index) {
    if (legs.length <= 2) {
      alert('Parlay must have at least 2 legs');
      return;
    }
    const newLegs = legs.filter((_, i) => i !== index);
    // Renumber
    newLegs.forEach((leg, i) => leg.number = i + 1);
    setLegs(newLegs);
  }

  function updateLeg(index, field, value) {
    const newLegs = [...legs];
    newLegs[index] = { ...newLegs[index], [field]: value };
    setLegs(newLegs);
  }

  function calculateParlayOdds(legs) {
    if (legs.some(leg => !leg.odds_american)) return 0;

    // Convert American to decimal
    const decimalOdds = legs.map(leg => {
      const american = parseInt(leg.odds_american);
      if (american > 0) {
        return (american / 100) + 1;
      } else {
        return (100 / Math.abs(american)) + 1;
      }
    });

    // Multiply all decimal odds
    const combinedDecimal = decimalOdds.reduce((acc, odds) => acc * odds, 1);

    // Convert back to American
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

  async function handleSubmit() {
    // Validation
    if (!selectedAccount) {
      alert('Please select an account');
      return;
    }
    if (!stake || parseFloat(stake) <= 0) {
      alert('Please enter a valid stake amount');
      return;
    }
    if (legs.some(leg => !leg.market_key || !leg.odds_american)) {
      alert('Please complete all leg details');
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/bankroll/parlays?user_id=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: parseInt(selectedAccount),
          stake_amount: parseFloat(stake),
          legs: legs.map(leg => ({
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
          notes
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create parlay');
      }

      const data = await response.json();
      onSave(data);
    } catch (error) {
      console.error('Error creating parlay:', error);
      alert(`Failed to create parlay: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  const sportMix = [...new Set(legs.map(leg => leg.sport))].join(' + ');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Build Parlay</h2>
          <p className="text-gray-600">
            {legs.length} Leg{legs.length !== 1 ? 's' : ''} • {sportMix}
          </p>
        </div>
        <Button variant="ghost" onClick={onCancel}>
          <X className="w-5 h-5" />
        </Button>
      </div>

      {/* Legs */}
      <div className="space-y-3">
        {legs.map((leg, index) => (
          <Card key={index} className="p-4 border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Leg {leg.number}</h3>
              {legs.length > 2 && (
                <button
                  onClick={() => removeLeg(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Sport */}
              <div>
                <label className="block text-sm font-medium mb-1">Sport</label>
                <select
                  value={leg.sport}
                  onChange={(e) => updateLeg(index, 'sport', e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="NFL">NFL</option>
                  <option value="NBA">NBA</option>
                  <option value="MLB">MLB</option>
                  <option value="NHL">NHL</option>
                  <option value="Soccer">Soccer</option>
                  <option value="Tennis">Tennis</option>
                </select>
              </div>

              {/* Bet Type */}
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={leg.bet_type}
                  onChange={(e) => updateLeg(index, 'bet_type', e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="player_prop">Player Prop</option>
                  <option value="game_line">Game Line</option>
                  <option value="team_prop">Team Prop</option>
                </select>
              </div>

              {/* Market */}
              <div>
                <label className="block text-sm font-medium mb-1">Market</label>
                <select
                  value={leg.market_key}
                  onChange={(e) => updateLeg(index, 'market_key', e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  {leg.sport === 'NFL' && (
                    <>
                      <option value="player_pass_yds">Pass Yards</option>
                      <option value="player_rush_yds">Rush Yards</option>
                      <option value="player_rec_yds">Rec Yards</option>
                      <option value="player_anytime_td">Anytime TD</option>
                      <option value="spread">Spread</option>
                      <option value="totals">Total Points</option>
                      <option value="moneyline">Moneyline</option>
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
                  {/* Add more sports as needed */}
                </select>
              </div>

              {/* Side */}
              <div>
                <label className="block text-sm font-medium mb-1">Side</label>
                <select
                  value={leg.bet_side}
                  onChange={(e) => updateLeg(index, 'bet_side', e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="over">Over</option>
                  <option value="under">Under</option>
                  <option value="home">Home</option>
                  <option value="away">Away</option>
                </select>
              </div>

              {/* Line */}
              <div>
                <label className="block text-sm font-medium mb-1">Line</label>
                <input
                  type="number"
                  step="0.5"
                  value={leg.line_value}
                  onChange={(e) => updateLeg(index, 'line_value', e.target.value)}
                  placeholder="275.5"
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              {/* Odds */}
              <div>
                <label className="block text-sm font-medium mb-1">Odds</label>
                <input
                  type="number"
                  value={leg.odds_american}
                  onChange={(e) => updateLeg(index, 'odds_american', e.target.value)}
                  placeholder="-110"
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              {/* Notes */}
              <div className="col-span-2">
                <label className="block text-sm font-medium mb-1">Notes</label>
                <input
                  type="text"
                  value={leg.notes}
                  onChange={(e) => updateLeg(index, 'notes', e.target.value)}
                  placeholder="Patrick Mahomes passing yards"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Add Leg Button */}
      <Button
        variant="secondary"
        onClick={addLeg}
        disabled={legs.length >= 15}
        className="w-full"
      >
        <Plus className="w-4 h-4 mr-2" />
        Add Leg {legs.length < 15 && `(${15 - legs.length} remaining)`}
      </Button>

      {/* Parlay Details */}
      <Card className="p-4 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center mb-3">
          <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="font-semibold">Parlay Summary</h3>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Legs</p>
            <p className="text-lg font-bold">{legs.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Sport Mix</p>
            <p className="text-lg font-bold">{sportMix}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Combined Odds</p>
            <p className="text-lg font-bold text-blue-600">
              {combinedOdds > 0 ? '+' : ''}{combinedOdds}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Potential Payout</p>
            <p className="text-lg font-bold text-green-600">
              ${potentialPayout.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Account & Stake */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1">Account</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select account...</option>
              {accounts.map(account => (
                <option key={account.account_id} value={account.account_id}>
                  {account.bookmaker_name} (${account.current_balance})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Stake ($)</label>
            <input
              type="number"
              step="0.01"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              placeholder="100.00"
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        {/* Notes */}
        <div className="mt-3">
          <label className="block text-sm font-medium mb-1">Parlay Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Super confident in these picks..."
            rows={2}
            className="w-full border rounded px-3 py-2"
          />
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          variant="ghost"
          onClick={onCancel}
          className="flex-1"
        >
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmit}
          disabled={submitting || !selectedAccount || !stake || legs.length < 2}
          className="flex-1"
        >
          {submitting ? 'Creating Parlay...' : `Place Parlay (+${combinedOdds})`}
        </Button>
      </div>
    </div>
  );
}
