import { Target, TrendingUp, Calendar } from 'lucide-react';
import Card from '../../ui/Card';

const GoalProgressCard = ({ goal }) => {
  if (!goal) return null;

  const progressPercentage = parseFloat(goal.progress_percentage) || 0;
  const isComplete = progressPercentage >= 100;
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(parseFloat(amount || 0));
  };

  return (
    <Card variant="glass" hover>
      <Card.Content className="py-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isComplete ? 'bg-emerald-500/20' : 'bg-blue-500/20'
            }`}>
              <Target className={`w-5 h-5 ${isComplete ? 'text-emerald-400' : 'text-blue-400'}`} />
            </div>
            <div>
              <h3 className="text-white font-semibold">
                {goal.goal_type ? goal.goal_type.charAt(0).toUpperCase() + goal.goal_type.slice(1) : 'Goal'}
              </h3>
              {goal.description && (
                <p className="text-xs text-slate-500">{goal.description}</p>
              )}
            </div>
          </div>
          {isComplete && (
            <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
              Complete!
            </span>
          )}
        </div>

        {/* Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Progress</span>
            <span className={`font-bold ${
              progressPercentage >= 100 ? 'text-emerald-400' : 
              progressPercentage >= 50 ? 'text-blue-400' : 
              'text-slate-400'
            }`}>
              {progressPercentage.toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-dark-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                isComplete ? 'bg-gradient-to-r from-emerald-500 to-teal-500' : 
                'bg-gradient-to-r from-blue-500 to-cyan-500'
              }`}
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-dark-700">
          <div>
            <p className="text-xs text-slate-500 mb-1">Current</p>
            <p className={`text-lg font-bold font-mono ${
              parseFloat(goal.current_progress || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {formatCurrency(goal.current_progress)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Target</p>
            <p className="text-lg font-bold font-mono text-white">
              {formatCurrency(goal.goal_amount)}
            </p>
          </div>
        </div>

        {/* Days Remaining */}
        {goal.days_remaining > 0 && (
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
            <Calendar className="w-3 h-3" />
            <span>{goal.days_remaining} days remaining</span>
          </div>
        )}
      </Card.Content>
    </Card>
  );
};

export default GoalProgressCard;
