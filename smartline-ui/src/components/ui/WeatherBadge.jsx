import { Cloud, CloudRain, CloudSnow, Wind, Zap, Sun, Thermometer } from 'lucide-react';
import Badge from './Badge';
import { cn } from '../../lib/utils';

/**
 * WeatherBadge - Displays weather severity with contextual icons
 * 
 * Props:
 * - severity: 0-100 score
 * - temp_f: Temperature in Fahrenheit
 * - wind_mph: Wind speed
 * - precip_prob: Precipitation probability (0-100)
 * - conditions: Weather conditions text
 * - is_cold, is_hot, is_windy, is_heavy_wind, is_rain_risk, is_storm_risk: Boolean flags
 * - size: 'sm' | 'md' | 'lg'
 * - showIcons: Whether to show weather condition icons
 */

const WeatherBadge = ({ 
  severity = 0,
  temp_f,
  wind_mph,
  precip_prob,
  conditions,
  is_cold = false,
  is_hot = false,
  is_windy = false,
  is_heavy_wind = false,
  is_rain_risk = false,
  is_storm_risk = false,
  size = 'md',
  showIcons = true,
  className
}) => {
  
  // Determine severity variant
  const getSeverityVariant = (score) => {
    if (score === 0) return 'default';
    if (score <= 2) return 'primary';
    if (score <= 4) return 'warning';
    return 'error';
  };
  
  // Determine severity label
  const getSeverityLabel = (score) => {
    if (score === 0) return 'Clear';
    if (score <= 2) return 'Moderate';
    if (score <= 4) return 'Severe';
    return 'Extreme';
  };
  
  // Get weather icons based on conditions
  const getWeatherIcons = () => {
    const icons = [];
    
    if (is_cold) icons.push({ Icon: CloudSnow, label: 'Cold', key: 'cold' });
    if (is_hot) icons.push({ Icon: Sun, label: 'Hot', key: 'hot' });
    if (is_storm_risk) icons.push({ Icon: Zap, label: 'Storm Risk', key: 'storm' });
    if (is_rain_risk) icons.push({ Icon: CloudRain, label: 'Rain Risk', key: 'rain' });
    if (is_heavy_wind) icons.push({ Icon: Wind, label: 'Heavy Wind', key: 'heavy-wind' });
    else if (is_windy) icons.push({ Icon: Wind, label: 'Windy', key: 'windy' });
    
    return icons;
  };
  
  const variant = getSeverityVariant(severity);
  const label = getSeverityLabel(severity);
  const icons = getWeatherIcons();
  
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Severity Badge */}
      <Badge variant={variant} size={size}>
        <Thermometer className="w-3 h-3 mr-1" />
        Severity {severity} - {label}
      </Badge>
      
      {/* Weather Condition Icons */}
      {showIcons && icons.length > 0 && (
        <div className="flex items-center gap-1">
          {icons.map(({ Icon, label, key }) => (
            <span 
              key={key}
              className="text-slate-400 hover:text-white transition-colors"
              title={label}
            >
              <Icon className="w-4 h-4" />
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default WeatherBadge;
