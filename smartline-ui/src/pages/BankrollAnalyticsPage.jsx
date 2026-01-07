import { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Calendar, 
  Target, 
  BookOpen, 
  TrendingUp, 
  Lightbulb,
  Download,
  Filter
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import DayOfWeekChart from '../components/bankroll/charts/DayOfWeekChart';
import TimeOfDayChart from '../components/bankroll/charts/TimeOfDayChart';
import MarketPerformanceTable from '../components/bankroll/charts/MarketPerformanceTable';
import InsightsGrid from '../components/bankroll/charts/InsightsGrid';
import PerformanceCharts from '../components/bankroll/PerformanceCharts';

const API_BASE = 'https://smartline-production.up.railway.app';

const AnalyticsPage = () => {
  const [activeSection, setActiveSection] = useState('overview');
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [overviewData, setOverviewData] = useState(null);
  const [timeAnalysis, setTimeAnalysis] = useState(null);
  const [marketAnalysis, setMarketAnalysis] = useState(null);
  const [insights, setInsights] = useState([]);

  useEffect(() => {
    fetchAllData();
  }, [timeRange]);

  const fetchAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchOverview(),
      fetchTimeAnalysis(),
      fetchMarketAnalysis(),
      fetchInsights()
    ]);
    setLoading(false);
  };

  const fetchOverview = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/analytics/overview?user_id=1&days=${timeRange}`);
      const data = await response.json();
      setOverviewData(data);
    } catch (error) {
      console.error('Error fetching overview:', error);
    }
  };

  const fetchTimeAnalysis = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/analytics/time-analysis?user_id=1&days=${timeRange}`);
      const data = await response.json();
      setTimeAnalysis(data);
    } catch (error) {
      console.error('Error fetching time analysis:', error);
    }
  };

  const fetchMarketAnalysis = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/analytics/market-deep-dive?user_id=1&days=${timeRange}`);
      const data = await response.json();
      setMarketAnalysis(data);
    } catch (error) {
      console.error('Error fetching market analysis:', error);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch(`${API_BASE}/bankroll/analytics/insights?user_id=1&days=${timeRange}`);
      const data = await response.json();
      setInsights(data.insights || []);
    } catch (error) {
      console.error('Error fetching insights:', error);
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

  const sections = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'time', label: 'Time Analysis', icon: Calendar },
    { id: 'markets', label: 'Markets', icon: Target },
    { id: 'bookmakers', label: 'Bookmakers', icon: BookOpen },
    { id: 'trends', label: 'Trends', icon: TrendingUp },
    { id: 'insights', label: 'Insights', icon: Lightbulb }
  ];

  return (
    <div className="flex flex-col lg:flex-row gap-6 pb-8">
      {/* Sidebar Navigation (Desktop) */}
      <aside className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-6 space-y-2">
          <div className="bg-dark-800 rounded-xl p-2 border border-dark-700">
            {sections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    activeSection === section.id
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                      : 'text-slate-400 hover:text-white hover:bg-dark-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{section.label}</span>
                </button>
              );
            })}
          </div>

          {/* Time Range Selector */}
          <Card variant="elevated">
            <Card.Header>
              <Card.Title className="text-sm">Time Range</Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="space-y-2">
                {[7, 30, 90, 365].map((days) => (
                  <button
                    key={days}
                    onClick={() => setTimeRange(days)}
                    className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      timeRange === days
                        ? 'bg-blue-500 text-white'
                        : 'bg-dark-700 text-slate-400 hover:bg-dark-600 hover:text-white'
                    }`}
                  >
                    Last {days} days
                  </button>
                ))}
              </div>
            </Card.Content>
          </Card>
        </div>
      </aside>

      {/* Tab Navigation (Mobile/Tablet) */}
      <div className="lg:hidden border-b border-dark-700 -mx-6 px-6 overflow-x-auto">
        <nav className="flex gap-6 min-w-max">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center gap-2 px-1 py-4 border-b-2 transition-colors whitespace-nowrap ${
                  activeSection === section.id
                    ? 'border-blue-500 text-white'
                    : 'border-transparent text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{section.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <main className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-display font-bold text-white mb-1">
              Analytics
            </h1>
            <p className="text-slate-400">
              Comprehensive insights into your betting performance
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="md">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </Button>
            <Button variant="outline" size="md">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Mobile Time Range */}
        <div className="lg:hidden mb-6">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {[7, 30, 90, 365].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  timeRange === days
                    ? 'bg-blue-500 text-white'
                    : 'bg-dark-800 text-slate-400 hover:bg-dark-700 hover:text-white'
                }`}
              >
                {days}D
              </button>
            ))}
          </div>
        </div>

        {/* Content Sections */}
        {activeSection === 'overview' && (
          <OverviewSection 
            data={overviewData} 
            loading={loading}
            formatCurrency={formatCurrency}
          />
        )}

        {activeSection === 'time' && (
          <TimeAnalysisSection 
            data={timeAnalysis} 
            loading={loading}
          />
        )}

        {activeSection === 'markets' && (
          <MarketsSection 
            data={marketAnalysis} 
            loading={loading}
          />
        )}

        {activeSection === 'bookmakers' && (
          <BookmakersSection loading={loading} timeRange={timeRange} />
        )}

        {activeSection === 'trends' && (
          <TrendsSection loading={loading} />
        )}

        {activeSection === 'insights' && (
          <InsightsSection 
            insights={insights} 
            loading={loading}
          />
        )}
      </main>
    </div>
  );
};

// Section Components
const OverviewSection = ({ data, loading, formatCurrency }) => {
  if (loading || !data) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-dark-800 rounded-lg animate-pulse"></div>
        ))}
      </div>
    );
  }

  const stats = [
    { label: 'Win Rate', value: `${data.win_rate}%`, change: null, color: 'blue' },
    { label: 'Total Profit/Loss', value: formatCurrency(data.total_profit_loss), change: null, color: parseFloat(data.total_profit_loss) >= 0 ? 'emerald' : 'red' },
    { label: 'ROI', value: `${data.roi}%`, change: null, color: parseFloat(data.roi) >= 0 ? 'emerald' : 'red' },
    { label: 'Total Bets', value: data.total_bets, change: null, color: 'slate' }
  ];

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card key={index} variant="glass" hover>
            <Card.Content className="py-6">
              <p className="text-sm text-slate-400 mb-2">{stat.label}</p>
              <p className={`text-3xl font-display font-bold text-${stat.color}-400`}>
                {stat.value}
              </p>
            </Card.Content>
          </Card>
        ))}
      </div>

      {/* Quick Summary */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Performance Summary</Card.Title>
          <Card.Description>
            {data.total_bets} bets placed • {data.pending_bets} pending
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Win Rate</span>
                <span className="text-white font-bold">{data.win_rate}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-500 h-2 rounded-full transition-all"
                  style={{ width: `${data.win_rate}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-dark-700">
              <div>
                <p className="text-xs text-slate-500 mb-1">Won</p>
                <p className="text-xl font-bold text-emerald-400">{data.won_bets}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Lost</p>
                <p className="text-xl font-bold text-red-400">{data.lost_bets}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Push</p>
                <p className="text-xl font-bold text-slate-400">{data.push_bets}</p>
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

const TimeAnalysisSection = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-96 bg-dark-800 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Day of Week */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Performance by Day of Week</Card.Title>
          <Card.Description>
            Identify your most profitable days
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <DayOfWeekChart data={data.by_day_of_week} height={350} />
        </Card.Content>
        {data.insights?.best_day && (
          <Card.Footer>
            <div className="text-sm text-slate-400">
              💡 <span className="text-white font-medium">{data.insights.best_day.day_name}</span> is your most profitable day
            </div>
          </Card.Footer>
        )}
      </Card>

      {/* Time of Day */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Performance by Time of Day</Card.Title>
          <Card.Description>
            When do you perform best?
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <TimeOfDayChart data={data.by_time_of_day} height={300} />
        </Card.Content>
        {data.insights?.best_time && (
          <Card.Footer>
            <div className="text-sm text-slate-400">
              💡 You're most profitable during <span className="text-white font-medium">{data.insights.best_time.time_period}</span>
            </div>
          </Card.Footer>
        )}
      </Card>
    </div>
  );
};

const MarketsSection = ({ data, loading }) => {
  if (loading || !data) {
    return <div className="h-96 bg-dark-800 rounded-lg animate-pulse"></div>;
  }

  return (
    <div className="space-y-6">
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Market Performance</Card.Title>
          <Card.Description>
            Detailed breakdown by market type
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <MarketPerformanceTable markets={data.markets} />
        </Card.Content>
      </Card>

      {/* Best/Worst Markets */}
      {data.best_markets && data.best_markets.length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card variant="glass" className="border-emerald-500/30">
            <Card.Header>
              <Card.Title className="text-emerald-400">Top Performing Markets</Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="space-y-3">
                {data.best_markets.map((market, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-white">{market.market_key}</span>
                    <span className="text-emerald-400 font-mono font-bold">
                      +${parseFloat(market.profit_loss).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </Card.Content>
          </Card>

          {data.worst_markets && data.worst_markets.length > 0 && (
            <Card variant="glass" className="border-red-500/30">
              <Card.Header>
                <Card.Title className="text-red-400">Struggling Markets</Card.Title>
              </Card.Header>
              <Card.Content>
                <div className="space-y-3">
                  {data.worst_markets.map((market, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-white">{market.market_key}</span>
                      <span className="text-red-400 font-mono font-bold">
                        ${parseFloat(market.profit_loss).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </Card.Content>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

const BookmakersSection = ({ loading, timeRange }) => {
  if (loading) {
    return <div className="h-96 bg-dark-800 rounded-lg animate-pulse"></div>;
  }

  return (
    <div className="space-y-6">
      <PerformanceCharts timeRange={timeRange} />
    </div>
  );
};

const TrendsSection = ({ loading }) => {
  if (loading) {
    return <div className="h-96 bg-dark-800 rounded-lg animate-pulse"></div>;
  }

  return (
    <Card variant="elevated">
      <Card.Header>
        <Card.Title>Coming Soon</Card.Title>
        <Card.Description>30/60/90 day trend analysis</Card.Description>
      </Card.Header>
      <Card.Content>
        <div className="text-center py-12">
          <TrendingUp className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">Trend analysis coming soon</p>
        </div>
      </Card.Content>
    </Card>
  );
};

const InsightsSection = ({ insights, loading }) => {
  if (loading) {
    return <div className="h-96 bg-dark-800 rounded-lg animate-pulse"></div>;
  }

  return (
    <div className="space-y-6">
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>AI-Powered Insights</Card.Title>
          <Card.Description>
            Personalized recommendations based on your betting history
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <InsightsGrid insights={insights} />
        </Card.Content>
      </Card>
    </div>
  );
};

export default AnalyticsPage;