import { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Activity,
  Plus,
  Wallet,
  PieChart,
  BarChart3,
  Calendar
} from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import AddBetModal from '../components/bankroll/AddBetModal';
import AddAccountModal from '../components/bankroll/AddAccountModal';
import RecentBets from '../components/bankroll/RecentBets';
import AccountsList from '../components/bankroll/AccountsList';

const API_BASE = 'https://smartline-production.up.railway.app';

const BankrollDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [showAddBet, setShowAddBet] = useState(false);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch overview data
  useEffect(() => {
    fetchOverview();
    fetchAccounts();
  }, []);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/bankroll/analytics/overview?user_id=1`);
      const data = await response.json();
      setOverview(data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    } finally {
      setLoading(false);
    }
  };


  const fetchAccounts = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/accounts?user_id=1`);
      const data = await response.json();
      setAccounts(data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const handleBetAdded = () => {
    fetchOverview();
    setShowAddBet(false);
  };

  const handleAccountAdded = () => {
    fetchAccounts();
    setShowAddAccount(false);
  };

  const refreshAll = async () => {
    setRefreshing(true);
    await Promise.all([fetchOverview(), fetchAccounts()]);
    setRefreshing(false);
  };

  // Format currency
  const formatCurrency = (amount) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  // Format percentage
  const formatPercent = (value) => {
    const num = parseFloat(value);
    return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`;
  };

  // Get streak display
  const getStreakDisplay = (streak) => {
    if (!streak || streak.length === 0) return null;
    
    const isWinStreak = streak.type === 'won';
    const icon = isWinStreak ? TrendingUp : TrendingDown;
    const color = isWinStreak ? 'emerald' : 'red';
    
    return {
      icon,
      color,
      text: `${streak.length} ${isWinStreak ? 'W' : 'L'}`,
      label: `${streak.length} ${isWinStreak ? 'win' : 'loss'} streak`
    };
  };

  const stats = overview ? [
    {
      label: 'Total Bankroll',
      value: formatCurrency(overview.total_bankroll),
      subtitle: formatCurrency(overview.available_balance) + ' available',
      icon: Wallet,
      color: 'primary',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Total Profit/Loss',
      value: formatCurrency(overview.total_profit_loss),
      subtitle: `ROI ${formatPercent(overview.roi)}`,
      icon: parseFloat(overview.total_profit_loss) >= 0 ? TrendingUp : TrendingDown,
      color: parseFloat(overview.total_profit_loss) >= 0 ? 'emerald' : 'red',
      gradient: parseFloat(overview.total_profit_loss) >= 0 
        ? 'from-emerald-500 to-teal-500' 
        : 'from-red-500 to-red-600'
    },
    {
      label: 'Win Rate',
      value: `${overview.win_rate}%`,
      subtitle: `${overview.won_bets}W - ${overview.lost_bets}L`,
      icon: Target,
      color: 'violet',
      gradient: 'from-violet-500 to-purple-500'
    },
    {
      label: 'Active Bets',
      value: overview.pending_bets.toString(),
      subtitle: formatCurrency(overview.locked_in_bets) + ' locked',
      icon: Activity,
      color: 'amber',
      gradient: 'from-amber-500 to-orange-500'
    },
  ] : [];

  const streakDisplay = overview?.current_streak ? getStreakDisplay(overview.current_streak) : null;

  return (
    <div className="space-y-8 pb-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <Wallet className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              Bankroll Manager
            </h1>
          </div>
          <p className="text-slate-400">
            Track your bets, manage your bankroll, and analyze your performance
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="ghost"
            size="md"
            onClick={refreshAll}
            disabled={refreshing}
          >
            <Activity className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button 
            variant="outline" 
            size="md"
            onClick={() => setShowAddAccount(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
          <Button 
            variant="primary" 
            size="md"
            onClick={() => setShowAddBet(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Log Bet
          </Button>
        </div>

      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {loading ? (
          // Loading skeletons
          [1, 2, 3, 4].map((i) => (
            <Card key={i} variant="glass" className="animate-pulse">
              <div className="h-32 bg-dark-800 rounded-lg"></div>
            </Card>
          ))
        ) : stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card 
              key={index} 
              variant="glass" 
              hover 
              className="animate-slide-up overflow-hidden"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="relative">
                {/* Gradient background */}
                <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.gradient} opacity-10 rounded-full blur-2xl -mr-8 -mt-8`}></div>
                
                <div className="relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-12 h-12 bg-gradient-to-br ${stat.gradient} rounded-lg flex items-center justify-center shadow-lg`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    {/* Streak badge on second card if exists */}
                    {index === 1 && streakDisplay && (
                      <Badge 
                        variant={streakDisplay.color === 'emerald' ? 'success' : 'error'} 
                        size="sm"
                      >
                        {streakDisplay.text}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
                  <p className="text-3xl font-display font-bold text-white mb-1">
                    {stat.value}
                  </p>
                  <p className="text-xs text-slate-500">{stat.subtitle}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Bets - Takes 2 columns */}
        <div className="lg:col-span-2">
          <RecentBets onBetUpdated={fetchOverview} />
        </div>

        {/* Accounts List - Takes 1 column */}
        <div>
          <AccountsList 
            accounts={accounts} 
            onAccountUpdated={fetchAccounts}
          />
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Coming Soon - Charts */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <BarChart3 className="w-5 h-5 text-blue-400 mr-2 inline" />
              Bankroll Chart
            </Card.Title>
            <Card.Description>
              Track your balance over time
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="h-48 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
              <div className="text-center">
                <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500">Chart visualization coming in Phase 2</p>
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Coming Soon - Performance Breakdown */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>
              <PieChart className="w-5 h-5 text-purple-400 mr-2 inline" />
              Performance Breakdown
            </Card.Title>
            <Card.Description>
              Analyze by sportsbook and market
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="h-48 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
              <div className="text-center">
                <PieChart className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500">Analytics coming in Phase 2</p>
              </div>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Modals */}
      {showAddBet && (
        <AddBetModal 
          onClose={() => setShowAddBet(false)}
          onBetAdded={handleBetAdded}
          accounts={accounts}
        />
      )}

      {showAddAccount && (
        <AddAccountModal 
          onClose={() => setShowAddAccount(false)}
          onAccountAdded={handleAccountAdded}
        />
      )}
    </div>
  );
};

export default BankrollDashboard;
