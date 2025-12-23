import { cn } from '../../lib/utils';

const Input = ({ 
  label,
  error,
  helperText,
  className,
  icon: Icon,
  ...props 
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-slate-300 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        {Icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
            <Icon className="w-5 h-5" />
          </div>
        )}
        
        <input
          className={cn(
            "w-full px-4 py-2.5 bg-dark-900 border rounded-lg",
            "text-slate-50 placeholder:text-slate-500",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
            "transition-all duration-200",
            error 
              ? "border-red-500 focus:ring-red-500" 
              : "border-dark-700 hover:border-dark-600",
            Icon && "pl-10",
            className
          )}
          {...props}
        />
      </div>
      
      {error && (
        <p className="mt-1.5 text-sm text-red-400">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="mt-1.5 text-sm text-slate-500">{helperText}</p>
      )}
    </div>
  );
};

export default Input;
