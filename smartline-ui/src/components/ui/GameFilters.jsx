import { Filter, Cloud, Home, AlertTriangle } from 'lucide-react';
import Badge from './Badge';
import { cn } from '../../lib/utils';

/**
 * GameFilters - Filter games by type and weather
 */
const GameFilters = ({ 
  activeFilter, 
  onFilterChange,
  counts = {},
  className 
}) => {
  
  const filters = [
    { 
      id: 'all', 
      label: 'All Games', 
      icon: Filter,
      count: counts.all || 0
    },
    { 
      id: 'outdoor', 
      label: 'Outdoor', 
      icon: Cloud,
      count: counts.outdoor || 0
    },
    { 
      id: 'dome', 
      label: 'Dome', 
      icon: Home,
      count: counts.dome || 0
    },
    { 
      id: 'severe', 
      label: 'Severe Weather', 
      icon: AlertTriangle,
      count: counts.severe || 0
    },
  ];
  
  return (
    <div className={cn("flex flex-wrap gap-3", className)}>
      {filters.map((filter) => {
        const Icon = filter.icon;
        const isActive = activeFilter === filter.id;
        
        return (
          <button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all",
              isActive
                ? "bg-primary-500/10 border-primary-500/50 text-primary-400"
                : "bg-dark-800 border-dark-700 text-slate-400 hover:text-white hover:border-dark-600"
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="font-medium">{filter.label}</span>
            {filter.count > 0 && (
              <Badge 
                variant={isActive ? "primary" : "default"} 
                size="sm"
              >
                {filter.count}
              </Badge>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default GameFilters;
