import { cn } from '../../lib/utils';

const Card = ({ 
  children, 
  className,
  variant = 'default',
  padding = 'md',
  hover = false,
  glow = false,
  ...props 
}) => {
  const baseStyles = "rounded-xl border transition-all duration-200";
  
  const variants = {
    default: "bg-dark-900 border-dark-700",
    elevated: "bg-dark-800 border-dark-700",
    glass: "bg-dark-900/50 backdrop-blur-sm border-dark-700/50",
    outline: "bg-transparent border-primary-500/30",
  };
  
  const paddings = {
    none: "p-0",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  };
  
  const hoverEffect = hover ? "hover:border-primary-500/50 hover:shadow-glow-sm cursor-pointer" : "";
  const glowEffect = glow ? "shadow-glow" : "";
  
  return (
    <div
      className={cn(
        baseStyles,
        variants[variant],
        paddings[padding],
        hoverEffect,
        glowEffect,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ children, className }) => (
  <div className={cn("mb-4 pb-4 border-b border-dark-700", className)}>
    {children}
  </div>
);

const CardTitle = ({ children, className }) => (
  <h3 className={cn("text-xl font-display font-semibold text-slate-50", className)}>
    {children}
  </h3>
);

const CardDescription = ({ children, className }) => (
  <p className={cn("text-sm text-slate-400 mt-1", className)}>
    {children}
  </p>
);

const CardContent = ({ children, className }) => (
  <div className={cn("", className)}>
    {children}
  </div>
);

const CardFooter = ({ children, className }) => (
  <div className={cn("mt-4 pt-4 border-t border-dark-700 flex items-center justify-between", className)}>
    {children}
  </div>
);

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;
