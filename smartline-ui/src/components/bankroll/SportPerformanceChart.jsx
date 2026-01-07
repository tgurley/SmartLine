import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from '../ui/Card';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * SportPerformanceChart Component
 * 
 * Displays performance breakdown by sport with:
 * - Profit/loss bar chart
 * - Win rate comparison
 * - ROI analysis
 * - Best/worst sport highlighting
 */
export function SportPerformanceChart({ timeRange = 30 }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState('profit'); // 'profit', 'winrate', 'roi'

  useEffect(() => {
    fetchSportData();
  }, [timeRange]);

  async function fetchSportData() {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/bankroll/analytics/by-sport?user_id=1&days=${timeRange}`
      );
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Error fetching sport analytics:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </Card>
    );
  }

  if (!data || !data.by_sport || data.by_sport.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Sport Performance</h3>
        <p className="text-gray-500 text-center py-12">
          No data available for this time period
        </p>
      </Card>
    );
  }

  // Prepare chart data based on selected metric
  const chartData = data.by_sport.map(sport => ({
    sport: sport.sport,
    value: metric === 'profit' ? sport.profit_loss :
           metric === 'winrate' ? sport.win_rate :
           sport.roi_percentage,
    total_bets: sport.total_bets,
    won_bets: sport.won_bets,
    profit_loss: sport.profit_loss,
    win_rate: sport.win_rate,
    roi_percentage: sport.roi_percentage,
    total_staked: sport.total_staked
  }));

  // Sort by selected metric
  chartData.sort((a, b) => b.value - a.value);

  // Get color for bar based on value
  function getBarColor(value) {
    if (metric === 'profit') {
      return value >= 0 ? '#10b981' : '#ef4444'; // green : red
    }
    return '#3b82f6'; // blue for win rate and ROI
  }

  // Custom tooltip
  function CustomTooltip({ active, payload }) {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-white p-4 rounded shadow-lg border">
        <h4 className="font-bold mb-2">{data.sport}</h4>
        <div className="space-y-1 text-sm">
          <p><span className="text-gray-600">Bets:</span> <b>{data.total_bets}</b> ({data.won_bets} won)</p>
          <p>
            <span className="text-gray-600">Profit/Loss:</span>{' '}
            <b className={data.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
              {data.profit_loss >= 0 ? '+' : ''}${data.profit_loss.toFixed(2)}
            </b>
          </p>
          <p><span className="text-gray-600">Win Rate:</span> <b>{data.win_rate}%</b></p>
          <p><span className="text-gray-600">ROI:</span> <b>{data.roi_percentage}%</b></p>
          <p><span className="text-gray-600">Total Staked:</span> ${data.total_staked.toFixed(2)}</p>
        </div>
      </div>
    );
  }

  const metricLabel = {
    profit: 'Profit/Loss ($)',
    winrate: 'Win Rate (%)',
    roi: 'ROI (%)'
  }[metric];

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Performance by Sport</h3>
          <p className="text-sm text-gray-600">
            Last {timeRange} days • {data.summary.total_bets} total bets
          </p>
        </div>

        {/* Metric Selector */}
        <div className="flex gap-2">
          <button
            onClick={() => setMetric('profit')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              metric === 'profit'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Profit/Loss
          </button>
          <button
            onClick={() => setMetric('winrate')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              metric === 'winrate'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Win Rate
          </button>
          <button
            onClick={() => setMetric('roi')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              metric === 'roi'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            ROI
          </button>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sport" />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="value" name={metricLabel}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={getBarColor(entry.value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Summary Cards */}
      {data.summary.best_sport && data.summary.worst_sport && (
        <div className="grid grid-cols-2 gap-4 mt-6">
          {/* Best Sport */}
          <div className="p-4 bg-green-50 rounded border border-green-200">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">Best Sport</span>
            </div>
            <p className="text-lg font-bold text-green-900">
              {data.summary.best_sport.sport}
            </p>
            <p className="text-sm text-green-700">
              +${data.summary.best_sport.profit_loss.toFixed(2)}
            </p>
          </div>

          {/* Worst Sport */}
          <div className="p-4 bg-red-50 rounded border border-red-200">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium text-red-800">Worst Sport</span>
            </div>
            <p className="text-lg font-bold text-red-900">
              {data.summary.worst_sport.sport}
            </p>
            <p className="text-sm text-red-700">
              ${data.summary.worst_sport.profit_loss.toFixed(2)}
            </p>
          </div>
        </div>
      )}

      {/* Detailed Stats Table */}
      <div className="mt-6">
        <h4 className="font-semibold mb-3">Detailed Breakdown</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">Sport</th>
                <th className="text-right p-2">Bets</th>
                <th className="text-right p-2">Win Rate</th>
                <th className="text-right p-2">Staked</th>
                <th className="text-right p-2">P/L</th>
                <th className="text-right p-2">ROI</th>
              </tr>
            </thead>
            <tbody>
              {data.by_sport.map(sport => (
                <tr key={sport.sport} className="border-t hover:bg-gray-50">
                  <td className="p-2 font-medium">{sport.sport}</td>
                  <td className="text-right p-2">
                    {sport.total_bets} <span className="text-gray-500">({sport.won_bets}W)</span>
                  </td>
                  <td className="text-right p-2">{sport.win_rate}%</td>
                  <td className="text-right p-2">${sport.total_staked.toFixed(2)}</td>
                  <td className={`text-right p-2 font-medium ${
                    sport.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sport.profit_loss >= 0 ? '+' : ''}${sport.profit_loss.toFixed(2)}
                  </td>
                  <td className={`text-right p-2 ${
                    sport.roi_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sport.roi_percentage >= 0 ? '+' : ''}{sport.roi_percentage}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
