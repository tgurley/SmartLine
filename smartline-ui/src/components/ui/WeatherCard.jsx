import { Cloud, Wind, Droplets, Thermometer, Eye, TrendingDown, TrendingUp } from 'lucide-react';
import Card from './Card';
import Badge from './Badge';
import WeatherBadge from './WeatherBadge';
import { cn } from '../../lib/utils';

/**
 * WeatherCard - Detailed weather information card
 * 
 * Props:
 * - weather: Weather observation object
 * - forecast: Boolean - is this a forecast or observed data
 * - impact: Optional impact analysis object { expectedPoints, actualPoints, difference }
 * - compact: Boolean - show compact version
 */

const WeatherCard = ({ 
  weather,
  forecast = true,
  impact = null,
  compact = false,
  className 
}) => {
  
  if (!weather) {
    return (
      <Card variant="elevated" padding="md" className={className}>
        <p className="text-slate-400 text-sm">No weather data available</p>
      </Card>
    );
  }
  
  const {
    temp_f,
    temp_c,
    wind_mph,
    precip_prob,
    precip_mm,
    conditions,
    weather_severity_score,
    is_cold,
    is_hot,
    is_windy,
    is_heavy_wind,
    is_rain_risk,
    is_storm_risk,
    observed_at_utc
  } = weather;
  
  // Compact version for game cards
  if (compact) {
    return (
      <div className={cn("flex flex-col gap-2", className)}>
        <WeatherBadge
          severity={weather_severity_score}
          temp_f={temp_f}
          wind_mph={wind_mph}
          precip_prob={precip_prob}
          conditions={conditions}
          is_cold={is_cold}
          is_hot={is_hot}
          is_windy={is_windy}
          is_heavy_wind={is_heavy_wind}
          is_rain_risk={is_rain_risk}
          is_storm_risk={is_storm_risk}
          size="sm"
        />
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Thermometer className="w-3 h-3" />
            {temp_f}°F
          </span>
          <span className="flex items-center gap-1">
            <Wind className="w-3 h-3" />
            {wind_mph}mph
          </span>
          {forecast && precip_prob > 0 && (
            <span className="flex items-center gap-1">
              <Droplets className="w-3 h-3" />
              {precip_prob}%
            </span>
          )}
          {!forecast && precip_mm > 0 && (
            <span className="flex items-center gap-1">
              <Droplets className="w-3 h-3" />
              {precip_mm}mm
            </span>
          )}
        </div>
      </div>
    );
  }
  
  // Full detailed version
  return (
    <Card variant="elevated" padding="lg" className={className}>
      <Card.Header>
        <Card.Title>
          {forecast ? 'Weather Forecast' : 'Actual Conditions'}
        </Card.Title>
        <Card.Description>
          {conditions || 'Conditions data unavailable'}
        </Card.Description>
      </Card.Header>
      
      <Card.Content>
        {/* Severity Badge */}
        <div className="mb-6">
          <WeatherBadge
            severity={weather_severity_score}
            temp_f={temp_f}
            wind_mph={wind_mph}
            precip_prob={precip_prob}
            conditions={conditions}
            is_cold={is_cold}
            is_hot={is_hot}
            is_windy={is_windy}
            is_heavy_wind={is_heavy_wind}
            is_rain_risk={is_rain_risk}
            is_storm_risk={is_storm_risk}
          />
        </div>
        
        {/* Weather Details Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500/10 rounded-lg flex items-center justify-center">
              <Thermometer className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Temperature</p>
              <p className="text-lg font-semibold text-white">
                {temp_f}°F ({temp_c}°C)
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-violet-500/10 rounded-lg flex items-center justify-center">
              <Wind className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Wind Speed</p>
              <p className="text-lg font-semibold text-white">
                {wind_mph} mph
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center">
              <Droplets className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">
                {forecast ? 'Precip Chance' : 'Precipitation'}
              </p>
              <p className="text-lg font-semibold text-white">
                {forecast ? `${precip_prob}%` : `${precip_mm || 0}mm`}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-500/10 rounded-lg flex items-center justify-center">
              <Eye className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Severity Score</p>
              <p className="text-lg font-semibold text-white">
                {weather_severity_score} / 100
              </p>
            </div>
          </div>
        </div>
        
        {/* Impact Analysis (for past games) */}
        {impact && !forecast && (
          <div className="p-4 bg-dark-800 rounded-lg border border-dark-700">
            <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-primary-400" />
              Post-Game Analysis
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Expected Points:</span>
                <span className="text-white font-medium">{impact.expectedPoints}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actual Points:</span>
                <span className="text-white font-medium">{impact.actualPoints}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Difference:</span>
                <span className={cn(
                  "font-semibold",
                  impact.difference < 0 ? "text-red-400" : "text-emerald-400"
                )}>
                  {impact.difference > 0 ? '+' : ''}{impact.difference}
                </span>
              </div>
              <div className="pt-2 mt-2 border-t border-dark-700">
                <Badge 
                  variant={impact.difference < -3 ? "success" : "default"}
                  size="sm"
                >
                  {impact.difference < -3 ? 'Under Hit ✓' : 'Within Expected Range'}
                </Badge>
              </div>
            </div>
          </div>
        )}
        
        {/* Smart Betting Alert (for forecasts) */}
        {forecast && weather_severity_score >= 3 && (
          <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/30">
            <h4 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2">
              <TrendingDown className="w-4 h-4" />
              Weather Impact Alert
            </h4>
            <p className="text-sm text-slate-300">
              Historical data shows games with severity {weather_severity_score} average{' '}
              <span className="font-semibold text-white">4.2 fewer points</span> than expected.
              Consider the UNDER.
            </p>
          </div>
        )}
      </Card.Content>
    </Card>
  );
};

export default WeatherCard;
