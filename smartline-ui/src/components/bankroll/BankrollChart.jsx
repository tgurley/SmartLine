import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const API_BASE = 'https://smartline-production.up.railway.app';

const BankrollChart = () => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    fetchChartData();
  }, [timeRange]);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE}/bankroll/analytics/chart-data?user_id=1&days=${timeRange}`
      );
      const data = await response.json();
      setChartData(data);
    } catch (error) {
      console.error('Error fetching chart data:', error);
      setChartData([]);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Calculate stats from chart data
  const stats = chartData.length > 0 ? {
    startBalance: parseFloat(chartData[0]?.balance || 0),
    endBalance: parseFloat(chartData[chartData.length - 1]?.balance || 0),
    highestBalance: Math.max(...chartData.map(d => parseFloat(d.balance))),
    lowestBalance: Math.min(...chartData.map(d => parseFloat(d.balance))),
    totalChange: parseFloat(chartData[chartData.length - 1]?.balance || 0) - parseFloat(chartData[0]?.balance || 0)
  } : null;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-3 shadow-xl">
          <p className="text-xs text-slate-400 mb-2">
            {formatDate(data.date)}
          </p>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Balance:</span>
              <span className="text-sm font-bold text-white">
                {formatCurrency(data.balance)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">P/L:</span>
              <span className={`text-sm font-bold ${
                parseFloat(data.profit_loss) >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {parseFloat(data.profit_loss) >= 0 ? '+' : ''}
                {formatCurrency(data.profit_loss)}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Bankroll Over Time</Card.Title>
          <Card.Description>Loading chart...</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-80 bg-dark-800 rounded-lg animate-pulse"></div>
        </Card.Content>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Bankroll Over Time</Card.Title>
          <Card.Description>Track your balance history</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-80 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
            <div className="text-center">
              <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 mb-1">No data available yet</p>
              <p className="text-sm text-slate-500">
                Add bets and settle them to see your bankroll trend
              </p>
            </div>
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
            <Card.Title>Bankroll Over Time</Card.Title>
            <Card.Description>
              {timeRange} day history
            </Card.Description>
          </div>
          
          {/* Time Range Selector */}
          <div className="flex gap-2">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  timeRange === days
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                    : 'bg-dark-800 text-slate-400 hover:bg-dark-700 hover:text-white'
                }`}
              >
                {days}D
              </button>
            ))}
          </div>
        </div>
      </Card.Header>

      <Card.Content>
        {/* Stats Row */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-dark-800 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Period Change</p>
              <div className="flex items-center gap-2">
                {stats.totalChange >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-400" />
                )}
                <span className={`text-lg font-bold font-mono ${
                  stats.totalChange >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {stats.totalChange >= 0 ? '+' : ''}{formatCurrency(stats.totalChange)}
                </span>
              </div>
            </div>

            <div className="bg-dark-800 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Current</p>
              <p className="text-lg font-bold font-mono text-white">
                {formatCurrency(stats.endBalance)}
              </p>
            </div>

            <div className="bg-dark-800 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Peak</p>
              <p className="text-lg font-bold font-mono text-blue-400">
                {formatCurrency(stats.highestBalance)}
              </p>
            </div>

            <div className="bg-dark-800 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">Low</p>
              <p className="text-lg font-bold font-mono text-slate-400">
                {formatCurrency(stats.lowestBalance)}
              </p>
            </div>
          </div>
        )}

        {/* Chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="#1e293b" 
                vertical={false}
              />
              
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#64748b"
                style={{ fontSize: '12px' }}
                tickLine={false}
              />
              
              <YAxis
                tickFormatter={formatCurrency}
                stroke="#64748b"
                style={{ fontSize: '12px' }}
                tickLine={false}
                axisLine={false}
              />
              
              <Tooltip content={<CustomTooltip />} />
              
              <Area
                type="monotone"
                dataKey="balance"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorBalance)"
                dot={false}
                activeDot={{ r: 6, fill: '#3b82f6', strokeWidth: 2, stroke: '#1e293b' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card.Content>

      <Card.Footer>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Balance trend</span>
        </div>
        <span className="text-sm text-slate-500">
          Last {timeRange} days
        </span>
      </Card.Footer>
    </Card>
  );
};

export default BankrollChart;
