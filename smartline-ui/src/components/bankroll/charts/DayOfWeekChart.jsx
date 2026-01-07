import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const DayOfWeekChart = ({ data, height = 300 }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
        <p className="text-slate-400">No data available</p>
      </div>
    );
  }

  // Ensure days are in correct order (Sun-Sat)
  const dayOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const sortedData = [...data].sort((a, b) => {
    return dayOrder.indexOf(a.day_name) - dayOrder.indexOf(b.day_name);
  });

  // Get color based on profit/loss
  const getBarColor = (value) => {
    const num = parseFloat(value);
    if (num > 0) return '#10b981'; // emerald-500
    if (num < 0) return '#ef4444'; // red-500
    return '#64748b'; // slate-500
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-3 shadow-xl">
          <p className="text-sm font-semibold text-white mb-2">{data.day_name}</p>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">P/L:</span>
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
                {data.wins}W - {data.losses}L
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Total Bets:</span>
              <span className="text-sm text-slate-300">
                {data.total_bets}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={sortedData}
        margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis
          dataKey="day_name"
          stroke="#64748b"
          style={{ fontSize: '12px' }}
          tickLine={false}
          tick={{ fill: '#94a3b8' }}
        />
        <YAxis
          tickFormatter={formatCurrency}
          stroke="#64748b"
          style={{ fontSize: '12px' }}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#94a3b8' }}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }} />
        <Bar dataKey="total_profit_loss" radius={[4, 4, 0, 0]}>
          {sortedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getBarColor(entry.total_profit_loss)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default DayOfWeekChart;
