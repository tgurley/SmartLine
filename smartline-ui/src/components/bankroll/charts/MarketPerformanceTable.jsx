import { TrendingUp, TrendingDown, Target } from 'lucide-react';

const MarketPerformanceTable = ({ markets }) => {
  if (!markets || markets.length === 0) {
    return (
      <div className="text-center py-12 bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
        <Target className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400">No market data available</p>
      </div>
    );
  }

  const formatCurrency = (amount) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  const formatMarketKey = (key) => {
    const names = {
      'player_pass_yds': 'Pass Yards',
      'player_pass_tds': 'Pass TDs',
      'player_rush_yds': 'Rush Yards',
      'player_reception_yds': 'Receiving Yards',
      'player_anytime_td': 'Anytime TD',
      'spread': 'Spread',
      'total': 'Total',
      'moneyline': 'Moneyline'
    };
    return names[key] || key;
  };

  const getMarketIcon = (key) => {
    const icons = {
      'player_pass_yds': '🎯',
      'player_pass_tds': '🏈',
      'player_rush_yds': '🏃',
      'player_reception_yds': '📊',
      'player_anytime_td': '⚡'
    };
    return icons[key] || '📈';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="border-b border-dark-700">
          <tr className="text-left text-xs text-slate-400 uppercase">
            <th className="pb-3 font-medium">Market</th>
            <th className="pb-3 font-medium text-center">Bets</th>
            <th className="pb-3 font-medium text-center">Win Rate</th>
            <th className="pb-3 font-medium text-center">ROI</th>
            <th className="pb-3 font-medium text-right">Profit/Loss</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((market, index) => {
            const pl = parseFloat(market.total_profit_loss);
            const winRate = parseFloat(market.win_rate);
            const roi = parseFloat(market.roi);
            
            return (
              <tr
                key={index}
                className="border-b border-dark-700 hover:bg-dark-800 transition-colors"
              >
                <td className="py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getMarketIcon(market.market_key)}</span>
                    <div>
                      <p className="text-white font-medium text-sm">
                        {formatMarketKey(market.market_key)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {market.won_bets}W - {market.lost_bets}L
                        {market.push_bets > 0 && ` - ${market.push_bets}P`}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="py-4 text-center">
                  <span className="text-white font-mono text-sm">
                    {market.total_bets}
                  </span>
                </td>
                <td className="py-4 text-center">
                  <div className="flex flex-col items-center">
                    <span className={`text-sm font-bold ${
                      winRate >= 60 ? 'text-emerald-400' :
                      winRate >= 50 ? 'text-blue-400' :
                      'text-slate-400'
                    }`}>
                      {winRate.toFixed(1)}%
                    </span>
                    <div className="w-16 bg-dark-700 rounded-full h-1 mt-1">
                      <div
                        className={`h-1 rounded-full ${
                          winRate >= 60 ? 'bg-emerald-500' :
                          winRate >= 50 ? 'bg-blue-500' :
                          'bg-slate-500'
                        }`}
                        style={{ width: `${Math.min(winRate, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </td>
                <td className="py-4 text-center">
                  <span className={`text-sm font-mono font-bold ${
                    roi > 0 ? 'text-emerald-400' : roi < 0 ? 'text-red-400' : 'text-slate-400'
                  }`}>
                    {roi > 0 ? '+' : ''}{roi.toFixed(1)}%
                  </span>
                </td>
                <td className="py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {pl > 0 ? (
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                    ) : pl < 0 ? (
                      <TrendingDown className="w-4 h-4 text-red-400" />
                    ) : null}
                    <span className={`font-mono font-bold text-sm ${
                      pl >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {pl >= 0 ? '+' : ''}{formatCurrency(pl)}
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default MarketPerformanceTable;
