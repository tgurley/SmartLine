import { Cloud, Wind, Droplets, Thermometer, AlertTriangle } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import WeatherBadge from '../ui/WeatherBadge';

/**
 * WeatherDetail - Comprehensive weather analysis for the game
 */
const WeatherDetail = ({ game }) => {
  const weather = game.weather;
  
  if (!weather || game.venue?.is_dome) {
    return (
      <Card variant="elevated" padding="lg">
        <div className="text-center py-12">
          <p className="text-slate-400">Weather data not available for indoor games</p>
        </div>
      </Card>
    );
  }
  
  const severity = weather.severity_score || 0;
  
  // Historical impact analysis (placeholder - would come from API)
  const historicalImpact = {
    similarGames: 12,
    avgTotalPoints: 42.3,
    expectedImpact: severity >= 3 ? -4.5 : -1.2,
    recommendation: severity >= 3 ? 'Consider UNDER' : 'Minimal impact expected'
  };
  
  return (
    <div className="space-y-6">
      {/* Weather Summary */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>Current Conditions</Card.Title>
          <Card.Description>Forecast for game time</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="mb-6">
            <WeatherBadge
              severity={severity}
              temp_f={weather.temp_f}
              wind_mph={weather.wind_mph}
              precip_prob={weather.precip_prob}
              is_cold={weather.flags?.cold}
              is_windy={weather.flags?.windy}
              is_heavy_wind={weather.flags?.heavy_wind}
              is_rain_risk={weather.flags?.rain_risk}
              is_storm_risk={weather.flags?.storm_risk}
              size="lg"
            />
          </div>
          
          {/* Detailed Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-dark-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Thermometer className="w-4 h-4 text-primary-400" />
                <p className="text-xs text-slate-400">Temperature</p>
              </div>
              <p className="text-2xl font-bold text-white">{weather.temp_f}°F</p>
            </div>
            
            <div className="p-4 bg-dark-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Wind className="w-4 h-4 text-violet-400" />
                <p className="text-xs text-slate-400">Wind Speed</p>
              </div>
              <p className="text-2xl font-bold text-white">{weather.wind_mph} mph</p>
            </div>
            
            <div className="p-4 bg-dark-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Droplets className="w-4 h-4 text-emerald-400" />
                <p className="text-xs text-slate-400">Precipitation</p>
              </div>
              <p className="text-2xl font-bold text-white">
                {weather.precip_prob || weather.precip_mm || 0}
                {weather.precip_prob ? '%' : 'mm'}
              </p>
            </div>
            
            <div className="p-4 bg-dark-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <p className="text-xs text-slate-400">Severity</p>
              </div>
              <p className="text-2xl font-bold text-white">{severity}</p>
            </div>
          </div>
        </Card.Content>
      </Card>
      
      {/* Weather Flags */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>Condition Flags</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="flex flex-wrap gap-3">
            {weather.flags?.cold && (
              <Badge variant="primary" size="md">
                ❄️ Cold Conditions
              </Badge>
            )}
            {weather.flags?.windy && (
              <Badge variant="warning" size="md">
                💨 Windy
              </Badge>
            )}
            {weather.flags?.heavy_wind && (
              <Badge variant="error" size="md">
                🌪️ Heavy Wind
              </Badge>
            )}
            {weather.flags?.rain_risk && (
              <Badge variant="primary" size="md">
                🌧️ Rain Risk
              </Badge>
            )}
            {weather.flags?.storm_risk && (
              <Badge variant="error" size="md">
                ⚡ Storm Risk
              </Badge>
            )}
            {!weather.flags?.cold && !weather.flags?.windy && !weather.flags?.rain_risk && (
              <Badge variant="success" size="md">
                ✅ Clear Conditions
              </Badge>
            )}
          </div>
        </Card.Content>
      </Card>
      
      {/* Historical Impact */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>Historical Impact Analysis</Card.Title>
          <Card.Description>
            Based on {historicalImpact.similarGames} similar weather conditions
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-dark-800 rounded-lg">
              <span className="text-slate-400">Similar Games</span>
              <span className="text-white font-semibold">{historicalImpact.similarGames}</span>
            </div>
            
            <div className="flex justify-between items-center p-4 bg-dark-800 rounded-lg">
              <span className="text-slate-400">Avg Total Points</span>
              <span className="text-white font-semibold">{historicalImpact.avgTotalPoints}</span>
            </div>
            
            <div className="flex justify-between items-center p-4 bg-dark-800 rounded-lg">
              <span className="text-slate-400">Expected Impact</span>
              <span className={`font-semibold ${historicalImpact.expectedImpact < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {historicalImpact.expectedImpact > 0 ? '+' : ''}{historicalImpact.expectedImpact} points
              </span>
            </div>
            
            {severity >= 3 && (
              <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
                  <div>
                    <p className="text-amber-400 font-semibold mb-1">Betting Recommendation</p>
                    <p className="text-slate-300 text-sm">{historicalImpact.recommendation}</p>
                    <p className="text-slate-400 text-xs mt-2">
                      Severe weather conditions typically result in lower scoring games
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card.Content>
      </Card>
      
      {/* Weather Source */}
      <Card variant="glass" padding="md">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Data Source:</span>
          <span className="text-white">{weather.source || 'Weather API'}</span>
        </div>
      </Card>
    </div>
  );
};

export default WeatherDetail;
