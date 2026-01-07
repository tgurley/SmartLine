import { useState, useEffect, useRef } from 'react';
import { 
  Bell, 
  X, 
  CheckCircle, 
  AlertTriangle, 
  TrendingDown, 
  TrendingUp,
  Target,
  Flame,
  DollarSign,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const API_BASE = 'https://smartline-production.up.railway.app';

const AlertCenter = ({ isOpen, onClose, triggerRef }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('unread');
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      fetchAlerts();
    }
  }, [isOpen, filter]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, triggerRef]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE}/bankroll/alerts?user_id=1&read=${filter === 'all' ? 'all' : 'false'}`
      );
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (alertId) => {
    try {
      await fetch(`${API_BASE}/bankroll/alerts/${alertId}/read`, {
        method: 'PUT'
      });
      fetchAlerts();
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch(`${API_BASE}/bankroll/alerts/mark-all-read?user_id=1`, {
        method: 'PUT'
      });
      fetchAlerts();
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const deleteAlert = async (alertId) => {
    try {
      await fetch(`${API_BASE}/bankroll/alerts/${alertId}`, {
        method: 'DELETE'
      });
      fetchAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const getAlertIcon = (type) => {
    const icons = {
      goal_achieved: <Target className="w-5 h-5" />,
      limit_warning: <AlertTriangle className="w-5 h-5" />,
      losing_streak: <TrendingDown className="w-5 h-5" />,
      winning_streak: <TrendingUp className="w-5 h-5" />,
      hot_streak: <Flame className="w-5 h-5" />,
      profit_milestone: <DollarSign className="w-5 h-5" />
    };
    return icons[type] || <Bell className="w-5 h-5" />;
  };

  const getAlertColor = (type) => {
    const colors = {
      goal_achieved: 'emerald',
      limit_warning: 'amber',
      losing_streak: 'red',
      winning_streak: 'emerald',
      hot_streak: 'orange',
      profit_milestone: 'green'
    };
    return colors[type] || 'blue';
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  if (!isOpen) return null;

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-full mt-2 w-96 max-w-[calc(100vw-2rem)] bg-dark-800 border border-dark-700 rounded-xl shadow-2xl z-50 animate-slide-down"
    >
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-white" />
            <h3 className="text-lg font-semibold text-white">Notifications</h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-red-500 text-white text-xs font-bold rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('unread')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              filter === 'unread'
                ? 'bg-blue-500 text-white'
                : 'bg-dark-700 text-slate-400 hover:text-white'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              filter === 'all'
                ? 'bg-blue-500 text-white'
                : 'bg-dark-700 text-slate-400 hover:text-white'
            }`}
          >
            All
          </button>
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="ml-auto px-3 py-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              Mark all read
            </button>
          )}
        </div>
      </div>

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-400 text-sm mt-2">Loading alerts...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-8 text-center">
            <Bell className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-700">
            {alerts.map((alert) => (
              <AlertItem
                key={alert.alert_id}
                alert={alert}
                onMarkRead={markAsRead}
                onDelete={deleteAlert}
                getIcon={getAlertIcon}
                getColor={getAlertColor}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {alerts.length > 0 && (
        <div className="p-3 border-t border-dark-700 bg-dark-900">
          <button className="w-full text-sm text-slate-400 hover:text-white transition-colors">
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
};

const AlertItem = ({ alert, onMarkRead, onDelete, getIcon, getColor }) => {
  const color = getColor(alert.alert_type);
  const icon = getIcon(alert.alert_type);

  const getTimeAgo = (dateString) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return 'Recently';
    }
  };

  return (
    <div
      className={`p-4 hover:bg-dark-700/50 transition-colors ${
        !alert.is_read ? 'bg-blue-500/5' : ''
      }`}
    >
      <div className="flex gap-3">
        {/* Icon */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-lg bg-${color}-500/20 flex items-center justify-center text-${color}-400`}
        >
          {icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p
              className={`text-sm ${
                !alert.is_read ? 'text-white font-medium' : 'text-slate-300'
              }`}
            >
              {alert.message}
            </p>
            {!alert.is_read && (
              <span className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-1"></span>
            )}
          </div>

          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-slate-500">
              <Clock className="w-3 h-3 inline mr-1" />
              {getTimeAgo(alert.created_at)}
            </span>

            <div className="flex gap-1">
              {!alert.is_read && (
                <button
                  onClick={() => onMarkRead(alert.alert_id)}
                  className="p-1 text-blue-400 hover:text-blue-300 transition-colors"
                  title="Mark as read"
                >
                  <CheckCircle className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => onDelete(alert.alert_id)}
                className="p-1 text-slate-500 hover:text-red-400 transition-colors"
                title="Dismiss"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertCenter;
