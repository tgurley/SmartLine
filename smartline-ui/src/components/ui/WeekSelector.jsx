import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';

/**
 * WeekSelector - Navigate between weeks with dropdown and arrows
 */
const WeekSelector = ({ 
  currentWeek, 
  onWeekChange, 
  minWeek = 1, 
  maxWeek = 18,
  className 
}) => {
  
  const handlePrevious = () => {
    if (currentWeek > minWeek) {
      onWeekChange(currentWeek - 1);
    }
  };
  
  const handleNext = () => {
    if (currentWeek < maxWeek) {
      onWeekChange(currentWeek + 1);
    }
  };
  
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* Previous Week Button */}
      <button
        onClick={handlePrevious}
        disabled={currentWeek <= minWeek}
        className="p-2 rounded-lg bg-dark-800 text-slate-400 hover:text-white hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous week"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      
      {/* Week Dropdown */}
      <div className="flex items-center gap-2">
        <label htmlFor="week-select" className="text-sm text-slate-400 font-medium">
          Week:
        </label>
        <select
          id="week-select"
          value={currentWeek}
          onChange={(e) => onWeekChange(Number(e.target.value))}
          className="px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all min-w-[100px]"
        >
          {Array.from({ length: maxWeek - minWeek + 1 }, (_, i) => minWeek + i).map((week) => (
            <option key={week} value={week}>
              Week {week}
            </option>
          ))}
        </select>
      </div>
      
      {/* Next Week Button */}
      <button
        onClick={handleNext}
        disabled={currentWeek >= maxWeek}
        className="p-2 rounded-lg bg-dark-800 text-slate-400 hover:text-white hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        aria-label="Next week"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
};

export default WeekSelector;
