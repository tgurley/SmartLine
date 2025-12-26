import { Wallet, TrendingUp, TrendingDown, Plus, Edit, Trash2 } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const AccountsList = ({ accounts, onAccountUpdated }) => {
  const formatCurrency = (amount) => {
    const num = parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(num);
  };

  const calculateProfitLoss = (current, starting) => {
    return parseFloat(current) - parseFloat(starting);
  };

  const getBookmakerColor = (name) => {
    const colors = {
      'DraftKings': 'from-emerald-500 to-teal-500',
      'FanDuel': 'from-blue-500 to-cyan-500',
      'BetMGM': 'from-amber-500 to-orange-500',
      'Caesars': 'from-purple-500 to-pink-500',
      'BetRivers': 'from-indigo-500 to-blue-500',
      'PointsBet': 'from-red-500 to-orange-500',
    };
    
    // Default gradient if bookmaker not in list
    return colors[name] || 'from-slate-500 to-slate-600';
  };

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex items-center justify-between w-full">
          <div>
            <Card.Title>
              <Wallet className="w-5 h-5 text-blue-400 mr-2 inline" />
              Sportsbook Accounts
            </Card.Title>
            <Card.Description>
              {accounts.length} {accounts.length === 1 ? 'account' : 'accounts'} tracked
            </Card.Description>
          </div>
        </div>
      </Card.Header>
      <Card.Content>
        {accounts.length === 0 ? (
          <div className="text-center py-8">
            <Wallet className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">No accounts added</p>
            <p className="text-sm text-slate-500 mb-4">
              Add your sportsbook accounts to start tracking
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {accounts.map((account, index) => {
              const profitLoss = calculateProfitLoss(
                account.current_balance, 
                account.starting_balance
              );
              const isProfit = profitLoss > 0;
              const isLoss = profitLoss < 0;
              const gradient = getBookmakerColor(account.bookmaker_name);

              return (
                <div
                  key={account.account_id}
                  className="group relative bg-dark-800 rounded-lg p-4 hover:bg-dark-700 transition-all border border-dark-700 hover:border-dark-600 animate-slide-up"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* Gradient background decoration */}
                  <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${gradient} opacity-5 rounded-full blur-2xl -mr-8 -mt-8`}></div>

                  <div className="relative flex items-start justify-between">
                    {/* Left: Account Info */}
                    <div className="flex-1 min-w-0">
                      {/* Bookmaker Icon & Name */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-10 h-10 bg-gradient-to-br ${gradient} rounded-lg flex items-center justify-center shadow-lg flex-shrink-0`}>
                          <Wallet className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-white font-semibold truncate">
                            {account.bookmaker_name}
                          </h3>
                          <p className="text-xs text-slate-500">
                            Since {new Date(account.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              year: 'numeric'
                            })}
                          </p>
                        </div>
                      </div>

                      {/* Balance */}
                      <div className="mb-2">
                        <p className="text-sm text-slate-400 mb-1">Current Balance</p>
                        <p className="text-2xl font-display font-bold text-white">
                          {formatCurrency(account.current_balance)}
                        </p>
                      </div>

                      {/* Profit/Loss */}
                      <div className="flex items-center gap-3">
                        <div>
                          <p className="text-xs text-slate-500 mb-0.5">Profit/Loss</p>
                          <div className="flex items-center gap-1">
                            {isProfit && <TrendingUp className="w-4 h-4 text-emerald-400" />}
                            {isLoss && <TrendingDown className="w-4 h-4 text-red-400" />}
                            <span className={`font-mono font-semibold ${
                              isProfit ? 'text-emerald-400' : 
                              isLoss ? 'text-red-400' : 
                              'text-slate-400'
                            }`}>
                              {isProfit ? '+' : ''}{formatCurrency(profitLoss)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="h-8 w-px bg-dark-700"></div>
                        
                        <div>
                          <p className="text-xs text-slate-500 mb-0.5">Starting</p>
                          <span className="text-sm font-mono text-slate-400">
                            {formatCurrency(account.starting_balance)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Right: Actions (shown on hover) */}
                    <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                      <button
                        className="p-1.5 text-slate-500 hover:text-blue-400 hover:bg-dark-900 rounded transition-colors"
                        title="Edit Account"
                        onClick={() => {
                          // TODO: Open edit modal
                          console.log('Edit account:', account.account_id);
                        }}
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-dark-900 rounded transition-colors"
                        title="Delete Account"
                        onClick={() => {
                          if (confirm(`Delete ${account.bookmaker_name} account?`)) {
                            // TODO: Implement delete
                            console.log('Delete account:', account.account_id);
                          }
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card.Content>
      <Card.Footer>
        <span className="text-sm text-slate-500">
          Total: {formatCurrency(
            accounts.reduce((sum, acc) => sum + parseFloat(acc.current_balance), 0)
          )}
        </span>
      </Card.Footer>
    </Card>
  );
};

export default AccountsList;
