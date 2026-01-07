import { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RotateCcw, 
  DollarSign, 
  Target, 
  Bell, 
  Shield, 
  TrendingUp,
  Wallet,
  User,
  Lock
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const API_BASE = 'https://smartline-production.up.railway.app';

// Default settings object
const DEFAULT_SETTINGS = {
  daily_limit: null,
  weekly_limit: null,
  monthly_limit: null,
  unit_size_type: 'fixed',
  unit_size_value: 100,
  max_bet_percentage: 5,
  enable_stop_loss: false,
  stop_loss_amount: null,
  enable_limit_alerts: true,
  enable_streak_alerts: true,
  alert_threshold_percentage: 80,
  daily_profit_goal: null,
  weekly_profit_goal: null,
  monthly_profit_goal: null
};

const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState('bankroll');
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [bankroll, setBankroll] = useState(0);
  const [recommendedUnit, setRecommendedUnit] = useState(null);

  useEffect(() => {
    if (activeTab === 'bankroll') {
      fetchSettings();
      fetchBankroll();
    }
  }, [activeTab]);

  useEffect(() => {
    if (settings && bankroll > 0) {
      calculateRecommendedUnit();
    }
  }, [settings, bankroll]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/bankroll/settings?user_id=1`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      alert('Could not load settings. Using defaults.');
    } finally {
      setLoading(false);
    }
  };

  const fetchBankroll = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/analytics/overview?user_id=1`);
      const data = await response.json();
      setBankroll(parseFloat(data.total_bankroll) || 0);
    } catch (error) {
      console.error('Error fetching bankroll:', error);
    }
  };

  const calculateRecommendedUnit = () => {
    if (!settings) return;
    
    if (settings.unit_size_type === 'fixed') {
      const percentage = bankroll > 0 ? (parseFloat(settings.unit_size_value) / bankroll * 100) : 0;
      setRecommendedUnit({
        amount: parseFloat(settings.unit_size_value),
        percentage: percentage.toFixed(2)
      });
    } else {
      const amount = bankroll * (parseFloat(settings.unit_size_value) / 100);
      setRecommendedUnit({
        amount: amount,
        percentage: parseFloat(settings.unit_size_value)
      });
    }
  };

  const handleChange = (field, value) => {
    setSettings({ ...settings, [field]: value });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE}/bankroll/settings?user_id=1`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save');
      }

      alert('Settings saved successfully!');
      fetchSettings();
    } catch (error) {
      console.error('Error saving settings:', error);
      alert(`Failed to save settings: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset all settings to defaults?')) return;

    try {
      const response = await fetch(`${API_BASE}/bankroll/settings/reset?user_id=1`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('Settings reset to defaults');
        fetchSettings();
      }
    } catch (error) {
      console.error('Error resetting settings:', error);
      alert('Failed to reset settings');
    }
  };

  const formatCurrency = (amount) => {
    const num = parseFloat(amount || 0);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(num);
  };

  const tabs = [
    { id: 'bankroll', label: 'Bankroll Manager', icon: Wallet },
    { id: 'account', label: 'Account', icon: User },
    { id: 'privacy', label: 'Privacy & Security', icon: Lock },
  ];

  return (
    <div className="space-y-8 pb-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <SettingsIcon className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              Settings
            </h1>
          </div>
          <p className="text-slate-400">
            Manage your account preferences and application settings
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-700">
        <nav className="flex gap-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-1 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'bankroll' && (
        <BankrollSettings
          settings={settings}
          loading={loading}
          saving={saving}
          bankroll={bankroll}
          recommendedUnit={recommendedUnit}
          onSave={handleSave}
          onReset={handleReset}
          onChange={handleChange}
          formatCurrency={formatCurrency}
        />
      )}

      {activeTab === 'account' && (
        <div className="text-center py-16">
          <User className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Account Settings</h3>
          <p className="text-slate-400">Coming soon</p>
        </div>
      )}

      {activeTab === 'privacy' && (
        <div className="text-center py-16">
          <Lock className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Privacy & Security</h3>
          <p className="text-slate-400">Coming soon</p>
        </div>
      )}
    </div>
  );
};

// Bankroll Settings Component
const BankrollSettings = ({ 
  settings, 
  loading, 
  saving, 
  bankroll, 
  recommendedUnit, 
  onSave, 
  onReset, 
  onChange,
  formatCurrency 
}) => {
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-64 bg-dark-800 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-8 bg-dark-800 rounded-lg text-center">
        <p className="text-red-400">Failed to load settings. Please refresh the page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" size="md" onClick={onReset}>
          <RotateCcw className="w-4 h-4 mr-2" />
          Reset to Defaults
        </Button>
        <Button variant="primary" size="md" onClick={onSave} disabled={saving}>
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {/* Unit Calculator Card */}
      {recommendedUnit && (
        <Card variant="glass" className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30">
          <Card.Content className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">Recommended Unit Size</p>
                  <p className="text-3xl font-display font-bold text-white">
                    {formatCurrency(recommendedUnit.amount)}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400 mb-1">Bankroll</p>
                <p className="text-xl font-bold text-white">{formatCurrency(bankroll)}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {recommendedUnit.percentage}% of bankroll
                </p>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Betting Limits */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <Shield className="w-5 h-5 text-blue-400 mr-2 inline" />
              Betting Limits
            </Card.Title>
            <Card.Description>
              Set maximum bet amounts to stay in control
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Daily Limit ($)
                </label>
                <input
                  type="number"
                  value={settings.daily_limit || ''}
                  onChange={(e) => onChange('daily_limit', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  min="0"
                  placeholder="No limit"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Weekly Limit ($)
                </label>
                <input
                  type="number"
                  value={settings.weekly_limit || ''}
                  onChange={(e) => onChange('weekly_limit', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  min="0"
                  placeholder="No limit"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Monthly Limit ($)
                </label>
                <input
                  type="number"
                  value={settings.monthly_limit || ''}
                  onChange={(e) => onChange('monthly_limit', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  min="0"
                  placeholder="No limit"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Max Bet (% of Bankroll)
                </label>
                <input
                  type="number"
                  value={settings.max_bet_percentage || ''}
                  onChange={(e) => onChange('max_bet_percentage', e.target.value ? parseFloat(e.target.value) : 5)}
                  step="0.5"
                  min="0.5"
                  max="100"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Maximum: {formatCurrency(bankroll * (parseFloat(settings.max_bet_percentage || 5) / 100))}
                </p>
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Unit Size Configuration */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <DollarSign className="w-5 h-5 text-emerald-400 mr-2 inline" />
              Unit Size
            </Card.Title>
            <Card.Description>
              Configure your standard bet size
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Unit Type
                </label>
                <select
                  value={settings.unit_size_type || 'fixed'}
                  onChange={(e) => onChange('unit_size_type', e.target.value)}
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="fixed">Fixed Amount</option>
                  <option value="percentage">Percentage of Bankroll</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {(settings.unit_size_type || 'fixed') === 'fixed' ? 'Amount ($)' : 'Percentage (%)'}
                </label>
                <input
                  type="number"
                  value={settings.unit_size_value || ''}
                  onChange={(e) => onChange('unit_size_value', parseFloat(e.target.value) || 0)}
                  step={(settings.unit_size_type || 'fixed') === 'fixed' ? '1' : '0.5'}
                  min={(settings.unit_size_type || 'fixed') === 'fixed' ? '1' : '0.5'}
                  max={(settings.unit_size_type || 'fixed') === 'percentage' ? '100' : undefined}
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div className="pt-4 border-t border-dark-700">
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium text-slate-300">
                    Enable Stop Loss
                  </label>
                  <button
                    onClick={() => onChange('enable_stop_loss', !settings.enable_stop_loss)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.enable_stop_loss ? 'bg-blue-500' : 'bg-dark-700'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.enable_stop_loss ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {settings.enable_stop_loss && (
                  <input
                    type="number"
                    value={settings.stop_loss_amount || ''}
                    onChange={(e) => onChange('stop_loss_amount', parseFloat(e.target.value) || null)}
                    placeholder="Stop loss amount"
                    step="1"
                    min="0"
                    className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                )}
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Profit Goals */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <Target className="w-5 h-5 text-amber-400 mr-2 inline" />
              Profit Goals
            </Card.Title>
            <Card.Description>
              Set targets to stay motivated
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Daily Profit Goal ($)
                </label>
                <input
                  type="number"
                  value={settings.daily_profit_goal || ''}
                  onChange={(e) => onChange('daily_profit_goal', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  placeholder="No goal"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Weekly Profit Goal ($)
                </label>
                <input
                  type="number"
                  value={settings.weekly_profit_goal || ''}
                  onChange={(e) => onChange('weekly_profit_goal', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  placeholder="No goal"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Monthly Profit Goal ($)
                </label>
                <input
                  type="number"
                  value={settings.monthly_profit_goal || ''}
                  onChange={(e) => onChange('monthly_profit_goal', e.target.value ? parseFloat(e.target.value) : null)}
                  step="1"
                  placeholder="No goal"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Notifications */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <Bell className="w-5 h-5 text-purple-400 mr-2 inline" />
              Notifications
            </Card.Title>
            <Card.Description>
              Configure alerts and warnings
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-300">Limit Alerts</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Warn when approaching betting limits
                  </p>
                </div>
                <button
                  onClick={() => onChange('enable_limit_alerts', !settings.enable_limit_alerts)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.enable_limit_alerts ? 'bg-blue-500' : 'bg-dark-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.enable_limit_alerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-dark-700">
                <div>
                  <p className="text-sm font-medium text-slate-300">Streak Alerts</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Notify on win/loss streaks
                  </p>
                </div>
                <button
                  onClick={() => onChange('enable_streak_alerts', !settings.enable_streak_alerts)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.enable_streak_alerts ? 'bg-blue-500' : 'bg-dark-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.enable_streak_alerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="pt-4 border-t border-dark-700">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Alert Threshold (%)
                </label>
                <input
                  type="number"
                  value={settings.alert_threshold_percentage || ''}
                  onChange={(e) => onChange('alert_threshold_percentage', parseFloat(e.target.value) || 80)}
                  step="5"
                  min="50"
                  max="100"
                  className="w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Alert when reaching {settings.alert_threshold_percentage || 80}% of any limit
                </p>
              </div>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Info Banner */}
      <Card variant="elevated" className="border-blue-500/30">
        <Card.Content className="py-6">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-1">Responsible Betting</h3>
              <p className="text-sm text-slate-400">
                Setting limits helps you bet responsibly. We recommend keeping individual bets to 1-5% of your total bankroll
                and setting realistic profit goals based on your betting history.
              </p>
            </div>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default SettingsPage;
