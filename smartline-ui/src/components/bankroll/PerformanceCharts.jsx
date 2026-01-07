import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import { TrendingUp, PieChart as PieIcon, Target } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

const API_BASE = 'https://smartline-production.up.railway.app';

const PerformanceCharts = ({ timeRange = 30 }) => {
  const [bookmakerData, setBookmakerData] = useState([]);
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPerformanceData();
  }, [timeRange]);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      const [bookmakerResponse, marketResponse] = await Promise.all([
        fetch(`${API_BASE}/bankroll/analytics/by-bookmaker?user_id=1&days=${timeRange}`),
        fetch(`${API_BASE}/bankroll/analytics/by-market?user_id=1&days=${timeRange}`)
      ]);

      const bookmakers = await bookmakerResponse.json();
      const markets = await marketResponse.json();

      setBookmakerData(bookmakers);
      setMarketData(markets);
    } catch (error) {
      console.error('Error fetching performance data:', error);
      setBookmakerData([]);
      setMarketData([]);
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

  const CustomTooltip = ({ active, payload, type }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-3 shadow-xl">
          <p className="text-sm font-semibold text-white mb-2">
            {type === 'bookmaker' ? data.bookmaker_name : formatMarketKey(data.market_key)}
          </p>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Profit/Loss:</span>
              <span className={`text-sm font-bold ${
                parseFloat(data.total_profit_loss) >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {formatCurrency(data.total_profit_loss)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Win Rate:</span>
              <span className="text-sm font-bold text-white">
                {parseFloat(data.win_rate).toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Record:</span>
              <span className="text-sm text-slate-300">
                {data.won_bets}W - {data.lost_bets}L
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Color scale for bars based on profit/loss
  const getBarColor = (value) => {
    const num = parseFloat(value);
    if (num > 0) return '#10b981'; // emerald-500
    if (num < 0) return '#ef4444'; // red-500
    return '#64748b'; // slate-500
  };

  // Colors for pie chart
  const PIE_COLORS = [
    '#3b82f6', // blue
    '#10b981', // emerald
    '#f59e0b', // amber
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
  ];

  if (loading) {
    return (
      <div className="grid md:grid-cols-2 gap-6">
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>Performance by Sportsbook</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="h-80 bg-dark-800 rounded-lg animate-pulse"></div>
          </Card.Content>
        </Card>
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>Performance by Market</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="h-80 bg-dark-800 rounded-lg animate-pulse"></div>
          </Card.Content>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Bookmaker Performance */}
      <Card variant="elevated">
        <Card.Header>
          <div>
            <Card.Title>
              <TrendingUp className="w-5 h-5 text-blue-400 mr-2 inline" />
              Performance by Sportsbook
            </Card.Title>
            <Card.Description>
              Profit/Loss across {bookmakerData.length} books
            </Card.Description>
          </div>
        </Card.Header>
        <Card.Content>
          {bookmakerData.length === 0 ? (
            <div className="h-80 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No bookmaker data yet</p>
              </div>
            </div>
          ) : (
            <>
              <div className="h-64 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={bookmakerData}
                    margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="bookmaker_name"
                      stroke="#64748b"
                      style={{ fontSize: '12px' }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      tickFormatter={formatCurrency}
                      stroke="#64748b"
                      style={{ fontSize: '12px' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip content={(props) => <CustomTooltip {...props} type="bookmaker" />} />
                    <Bar dataKey="total_profit_loss" radius={[4, 4, 0, 0]}>
                      {bookmakerData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getBarColor(entry.total_profit_loss)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Bookmaker Stats Table */}
              <div className="space-y-2">
                {bookmakerData.slice(0, 3).map((book, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-dark-800 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-white">
                        {book.bookmaker_name || 'Manual Entry'}
                      </span>
                      <Badge variant="default" size="sm">
                        {book.total_bets} bets
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-slate-400">
                        {parseFloat(book.win_rate).toFixed(1)}% WR
                      </span>
                      <span className={`font-bold font-mono ${
                        parseFloat(book.total_profit_loss) >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {parseFloat(book.total_profit_loss) >= 0 ? '+' : ''}
                        {formatCurrency(book.total_profit_loss)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card.Content>
      </Card>

      {/* Market Performance */}
      <Card variant="elevated">
        <Card.Header>
          <div>
            <Card.Title>
              <Target className="w-5 h-5 text-purple-400 mr-2 inline" />
              Performance by Market
            </Card.Title>
            <Card.Description>
              Win rates across {marketData.length} markets
            </Card.Description>
          </div>
        </Card.Header>
        <Card.Content>
          {marketData.length === 0 ? (
            <div className="h-80 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
              <div className="text-center">
                <PieIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No market data yet</p>
              </div>
            </div>
          ) : (
            <>
              <div className="h-64 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={marketData}
                    margin={{ top: 10, right: 10, left: 0, bottom: 50 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="market_key"
                      tickFormatter={formatMarketKey}
                      stroke="#64748b"
                      style={{ fontSize: '11px' }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      tickFormatter={formatCurrency}
                      stroke="#64748b"
                      style={{ fontSize: '12px' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip content={(props) => <CustomTooltip {...props} type="market" />} />
                    <Bar dataKey="total_profit_loss" radius={[4, 4, 0, 0]}>
                      {marketData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getBarColor(entry.total_profit_loss)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Top Performing & Struggling Markets */}
              <div className="grid md:grid-cols-2 gap-4">
                {/* Top Performing Markets */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-emerald-400 mb-3">Top Performing Markets</h4>
                  {marketData
                    .filter(market => parseFloat(market.total_profit_loss) > 0)
                    .sort((a, b) => parseFloat(b.total_profit_loss) - parseFloat(a.total_profit_loss))
                    .slice(0, 3)
                    .map((market, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-dark-800 rounded-lg border border-emerald-500/20"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-white">
                            {formatMarketKey(market.market_key)}
                          </span>
                        </div>
                        <span className="font-bold font-mono text-emerald-400">
                          +{formatCurrency(market.total_profit_loss)}
                        </span>
                      </div>
                    ))}
                  {marketData.filter(m => parseFloat(m.total_profit_loss) > 0).length === 0 && (
                    <p className="text-sm text-slate-500 text-center py-4">No profitable markets yet</p>
                  )}
                </div>

                {/* Struggling Markets */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-red-400 mb-3">Struggling Markets</h4>
                  {marketData
                    .filter(market => parseFloat(market.total_profit_loss) < 0)
                    .sort((a, b) => parseFloat(a.total_profit_loss) - parseFloat(b.total_profit_loss))
                    .slice(0, 3)
                    .map((market, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-dark-800 rounded-lg border border-red-500/20"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-white">
                            {formatMarketKey(market.market_key)}
                          </span>
                        </div>
                        <span className="font-bold font-mono text-red-400">
                          {formatCurrency(market.total_profit_loss)}
                        </span>
                      </div>
                    ))}
                  {marketData.filter(m => parseFloat(m.total_profit_loss) < 0).length === 0 && (
                    <p className="text-sm text-slate-500 text-center py-4">No losing markets 🎉</p>
                  )}
                </div>
              </div>
            </>
          )}
        </Card.Content>
      </Card>
    </div>
  );
};

export default PerformanceCharts;