import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, TrendingUp, BarChart3, BarChart2 } from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { icon: Home, label: 'Home', path: '/dashboard' },
  { icon: Calendar, label: 'Games', path: '/games' },
  { icon: TrendingUp, label: 'Odds', path: '/odds' },
  { icon: BarChart3, label: 'Stats', path: '/analytics' },
];

const MobileNav = () => {
  const location = useLocation();
  
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-dark-950/95 backdrop-blur-sm border-t border-dark-700">
      <div className="flex items-center justify-around px-2 py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-4 py-2 rounded-lg min-w-[70px]",
                "transition-all duration-200",
                isActive 
                  ? "bg-primary-500/10 text-primary-400" 
                  : "text-slate-400 active:bg-dark-800"
              )}
            >
              <Icon className={cn(
                "w-5 h-5",
                isActive && "text-primary-400"
              )} />
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;
