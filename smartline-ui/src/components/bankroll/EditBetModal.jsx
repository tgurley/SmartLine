import { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const EditBetModal = ({ bet, onClose, onBetUpdated, accounts }) => {
  const [formData, setFormData] = useState({
    account_id: bet.account_id || '',
    market_key: bet.market_key || '',
    bet_side: bet.bet_side || '',
    line_value: bet.line_value || '',
    odds_american: bet.odds_american || '',
    stake_amount: bet.stake_amount || '',
    notes: bet.notes || ''
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      
      // Prepare update data (only send changed fields)
      const updateData = {};
      
      if (formData.account_id !== (bet.account_id || '')) {
        updateData.account_id = formData.account_id ? parseInt(formData.account_id) : null;
      }
      if (formData.market_key !== (bet.market_key || '')) {
        updateData.market_key = formData.market_key;
      }
      if (formData.bet_side !== (bet.bet_side || '')) {
        updateData.bet_side = formData.bet_side;
      }
      if (formData.line_value !== (bet.line_value || '')) {
        updateData.line_value = parseFloat(formData.line_value);
      }
      if (formData.odds_american !== bet.odds_american) {
        updateData.odds_american = parseInt(formData.odds_american);
      }
      if (formData.stake_amount !== bet.stake_amount) {
        updateData.stake_amount = parseFloat(formData.stake_amount);
      }
      if (formData.notes !== (bet.notes || '')) {
        updateData.notes = formData.notes;
      }

      if (Object.keys(updateData).length === 0) {
        alert('No changes to save');
        return;
      }

      const response = await fetch(`${API_BASE}/bankroll/bets/${bet.bet_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        onBetUpdated();
        onClose();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to update bet');
      }
    } catch (error) {
      console.error('Error updating bet:', error);
      alert('Failed to update bet');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-dark-900 border-b border-dark-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-display font-bold text-white">
              Edit Bet
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              {bet.player_name || 'Game Bet'} • {bet.market_key}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Info Banner */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
            <p className="text-sm text-amber-300">
              ⚠️ Only pending bets can be edited. Changes to stake or odds will recalculate the potential payout.
            </p>
          </div>

          {/* Account Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Sportsbook Account
            </label>
            <select
              name="account_id"
              value={formData.account_id}
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
              Notes
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
              <Save className="w-4 h-4 mr-2" />
              {submitting ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditBetModal;
