import { X, AlertTriangle, CheckCircle, Info, AlertCircle } from 'lucide-react';

const AlertBanner = ({ alert, onDismiss }) => {
  if (!alert) return null;

  const getVariant = (type) => {
    const variants = {
      success: {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        icon: CheckCircle,
        iconColor: 'text-emerald-400',
        textColor: 'text-emerald-300'
      },
      warning: {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        icon: AlertTriangle,
        iconColor: 'text-amber-400',
        textColor: 'text-amber-300'
      },
      error: {
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        icon: AlertCircle,
        iconColor: 'text-red-400',
        textColor: 'text-red-300'
      },
      info: {
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        icon: Info,
        iconColor: 'text-blue-400',
        textColor: 'text-blue-300'
      }
    };
    return variants[type] || variants.info;
  };

  const variant = getVariant(alert.type);
  const Icon = variant.icon;

  return (
    <div className={`${variant.bg} ${variant.border} border rounded-lg p-4 animate-slide-down`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${variant.iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <p className={`text-sm font-medium ${variant.textColor}`}>
            {alert.message}
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default AlertBanner;
