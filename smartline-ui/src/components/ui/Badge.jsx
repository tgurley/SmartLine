import { cn } from '../../lib/utils';

const Badge = ({ 
  children, 
  variant = 'default',
  size = 'md',
  className,
  ...props 
}) => {
  const baseStyles = "inline-flex items-center justify-center font-medium rounded-full";
  
  const variants = {
    default: "bg-dark-800 text-slate-300 border border-dark-700",
    primary: "bg-primary-500/10 text-primary-400 border border-primary-500/30",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-400 border border-amber-500/30",
    error: "bg-red-500/10 text-red-400 border border-red-500/30",
    violet: "bg-violet-500/10 text-violet-400 border border-violet-500/30",
  };
  
  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  };
  
  return (
    <span
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
