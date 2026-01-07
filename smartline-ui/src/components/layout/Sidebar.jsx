import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Calendar, 
  TrendingUp,
  BarChart2, 
  BarChart3,
  Target,
  Trophy,
  Settings,
  Wallet,
  X
} from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { icon: Home, label: 'Dashboard', path: '/dashboard' },
  { icon: Calendar, label: 'Games', path: '/games' },
  { icon: TrendingUp, label: 'Odds', path: '/odds' },
  { icon: BarChart3, label: 'Analytics', path: '/analytics' },
  { icon: Trophy, label: 'Standings', path: '/standings' },
  { icon: Wallet, label: 'Bankroll Manager', path: '/bankroll' },
  { icon: BarChart2, label: 'Bankroll Analytics', path: '/bankroll/analytics' },
  { icon: Target, label: 'Goals', path: '/bankroll/goals' },
];

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={cn(
        "fixed top-0 left-0 z-50 h-full bg-dark-950 border-r border-dark-700",
        "transition-transform duration-300 ease-in-out",
        "lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)]",
        "w-64",
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        <div className="flex flex-col h-full">
          
          {/* Mobile Header */}
          <div className="flex items-center justify-between p-4 border-b border-dark-700 lg:hidden">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">SL</span>
              </div>
              <span className="font-display font-bold text-xl text-white">
                SmartLine
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => onClose()}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                    "group",
                    isActive 
                      ? "bg-primary-500/10 text-primary-400 border border-primary-500/30" 
                      : "text-slate-400 hover:text-white hover:bg-dark-800"
                  )}
                >
                  <Icon className={cn(
                    "w-5 h-5 transition-transform duration-200",
                    isActive && "text-primary-400",
                    !isActive && "group-hover:scale-110"
                  )} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>
          
          {/* Bottom Section */}
          <div className="p-4 border-t border-dark-700">
            <Link
              to="/settings"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-dark-800 transition-colors"
            >
              <Settings className="w-5 h-5" />
              <span className="font-medium">Settings</span>
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
