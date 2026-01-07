import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Calendar, 
  Target, 
  Shield, 
  AlertCircle,
  Flame
} from 'lucide-react';

const InsightCard = ({ insight }) => {
  const getIcon = (iconName) => {
    const icons = {
      'trending-up': TrendingUp,
      'trending-down': TrendingDown,
      'alert-triangle': AlertTriangle,
      'calendar': Calendar,
      'target': Target,
      'shield': Shield,
      'alert-circle': AlertCircle,
      'fire': Flame
    };
    return icons[iconName] || AlertCircle;
  };

  const getVariantStyles = (type) => {
    const variants = {
      success: {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        iconBg: 'bg-emerald-500/20',
        iconColor: 'text-emerald-400',
        textColor: 'text-emerald-300'
      },
      warning: {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        iconBg: 'bg-amber-500/20',
        iconColor: 'text-amber-400',
        textColor: 'text-amber-300'
      },
      error: {
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        iconBg: 'bg-red-500/20',
        iconColor: 'text-red-400',
        textColor: 'text-red-300'
      },
      info: {
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        iconBg: 'bg-blue-500/20',
        iconColor: 'text-blue-400',
        textColor: 'text-blue-300'
      }
    };
    return variants[type] || variants.info;
  };

  const Icon = getIcon(insight.icon);
  const styles = getVariantStyles(insight.type);

  return (
    <div className={`${styles.bg} ${styles.border} border rounded-lg p-4 transition-all hover:scale-[1.02]`}>
      <div className="flex gap-3">
        <div className={`${styles.iconBg} rounded-lg p-2 h-fit`}>
          <Icon className={`w-5 h-5 ${styles.iconColor}`} />
        </div>
        <div className="flex-1">
          <h4 className="text-white font-semibold text-sm mb-1">
            {insight.title}
          </h4>
          <p className={`text-sm ${styles.textColor}`}>
            {insight.message}
          </p>
        </div>
      </div>
    </div>
  );
};

const InsightsGrid = ({ insights }) => {
  if (!insights || insights.length === 0) {
    return (
      <div className="text-center py-12 bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
        <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400">No insights available yet</p>
        <p className="text-sm text-slate-500 mt-1">Log more bets to see personalized insights</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {insights.map((insight, index) => (
        <InsightCard key={index} insight={insight} />
      ))}
    </div>
  );
};

export { InsightCard, InsightsGrid };
export default InsightsGrid;
