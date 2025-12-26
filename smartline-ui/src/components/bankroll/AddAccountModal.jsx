import { useState } from 'react';
import { X, Wallet } from 'lucide-react';
import Button from '../ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

const AddAccountModal = ({ onClose, onAccountAdded }) => {
  const [formData, setFormData] = useState({
    bookmaker_name: '',
    starting_balance: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const popularBooks = [
    'DraftKings',
    'FanDuel',
    'BetMGM',
    'Caesars',
    'BetRivers',
    'PointsBet',
    'ESPN BET',
    'Fanatics',
    'Other'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleQuickSelect = (bookmaker) => {
    setFormData({ ...formData, bookmaker_name: bookmaker });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.bookmaker_name.trim()) {
      alert('Please enter a sportsbook name');
      return;
    }

    if (!formData.starting_balance || parseFloat(formData.starting_balance) <= 0) {
      alert('Please enter a valid starting balance');
      return;
    }

    try {
      setSubmitting(true);
      
      const accountData = {
        bookmaker_name: formData.bookmaker_name.trim(),
        starting_balance: parseFloat(formData.starting_balance)
      };

      const response = await fetch(`${API_BASE}/bankroll/accounts?user_id=1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountData)
      });

      if (response.ok) {
        onAccountAdded();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add account');
      }
    } catch (error) {
      console.error('Error adding account:', error);
      alert('Failed to add account');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-dark-900 border border-dark-700 rounded-xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="bg-dark-900 border-b border-dark-700 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-display font-bold text-white">
              Add Sportsbook Account
            </h2>
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
          {/* Quick Select */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Select Sportsbook
            </label>
            <div className="grid grid-cols-3 gap-2">
              {popularBooks.map((book) => (
                <button
                  key={book}
                  type="button"
                  onClick={() => handleQuickSelect(book)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    formData.bookmaker_name === book
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                      : 'bg-dark-800 text-slate-400 hover:bg-dark-700 hover:text-white border border-dark-700'
                  }`}
                >
                  {book}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Name (if Other selected or manual entry) */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Sportsbook Name
            </label>
            <input
              type="text"
              name="bookmaker_name"
              value={formData.bookmaker_name}
              onChange={handleChange}
              required
              placeholder="Enter sportsbook name..."
              className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-slate-500">
              Select from above or type a custom name
            </p>
          </div>

          {/* Starting Balance */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Starting Balance ($)
            </label>
            <input
              type="number"
              name="starting_balance"
              value={formData.starting_balance}
              onChange={handleChange}
              required
              step="0.01"
              min="0.01"
              placeholder="e.g., 1000.00"
              className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-slate-500">
              How much are you depositing to start with?
            </p>
          </div>

          {/* Info Box */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <Wallet className="w-4 h-4 text-blue-400" />
                </div>
              </div>
              <div className="flex-1">
                <p className="text-sm text-blue-300 font-medium mb-1">
                  Track Multiple Books
                </p>
                <p className="text-xs text-blue-400/80">
                  You can add multiple sportsbook accounts to compare performance and manage your overall bankroll across platforms.
                </p>
              </div>
            </div>
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
              {submitting ? 'Adding...' : 'Add Account'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddAccountModal;
