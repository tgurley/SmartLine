import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, TrendingUp, ChevronDown, ChevronUp, ExternalLink, ArrowRight } from 'lucide-react';
import Card from './Card';
import Badge from './Badge';
import Button from './Button';
import WeatherBadge from './WeatherBadge';
import TeamHelmet from './TeamHelmet';
import { cn } from '../../lib/utils';

/**
 * GameCard - Enhanced game card with weather and odds integration
 */

const GameCard = ({ 
  game,
  odds = null, // Pass odds data if available
  showWeather = true,
  showOdds = true,
  compact = false,
  className 
}) => {
  const [weatherExpanded, setWeatherExpanded] = useState(false);
  
  if (!game) return null;
  
  const {
    game_id,
    away_team,
    home_team,
    kickoff_utc,
    venue,
    result,
    weather,
    status
  } = game;
  
  // Format game date/time
  const gameDate = new Date(kickoff_utc);
  const isUpcoming = gameDate > new Date();
  const isFinal = status === 'final' || result !== null;
  
  const dateStr = gameDate.toLocaleDateString('en-US', { 
    weekday: 'short', 
    month: 'short', 
    day: 'numeric' 
  });
  const timeStr = gameDate.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
  });
  
  // Determine if game is in dome
  const isDome = venue?.is_dome;
  const hasWeather = weather && !isDome;
  const weatherSeverity = weather?.severity_score || 0;
  
  return (
    <Card 
      variant="elevated" 
      hover 
      padding="md"
      className={cn("transition-all duration-200", className)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {isDome && (
              <Badge variant="default" size="sm">
                <MapPin className="w-3 h-3 mr-1" />
                Dome
              </Badge>
            )}
            {isFinal && (
              <Badge variant="success" size="sm">
                Final
              </Badge>
            )}
            {!isFinal && isUpcoming && (
              <Badge variant="primary" size="sm">
                Scheduled
              </Badge>
            )}
          </div>
          
          {/* Game Time */}
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-3">
            <Calendar className="w-4 h-4" />
            <span>{dateStr} • {timeStr}</span>
          </div>
          
          {/* Teams */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TeamHelmet teamId={away_team.team_id} />
                <span className="text-lg font-display font-bold text-white">
                  {away_team.abbrev}
                </span>
                <span className="text-sm text-slate-500">{away_team.name}</span>
              </div>
              {result && (
                <span className="text-2xl font-bold text-white">
                  {result.away_score}
                </span>
              )}
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TeamHelmet teamId={home_team.team_id} />
                <span className="text-lg font-display font-bold text-white">
                  {home_team.abbrev}
                </span>
                <span className="text-sm text-slate-500">{home_team.name}</span>
              </div>
              {result && (
                <span className="text-2xl font-bold text-white">
                  {result.home_score}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Odds Section (if available) */}
      {showOdds && odds && (
        <div className="border-t border-dark-700 pt-4 mt-4">
          <div className="grid grid-cols-3 gap-4 mb-3">
            {/* Spread */}
            <div className="text-center p-3 bg-dark-800 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">Spread</p>
              <p className="text-sm font-semibold text-white">
                {home_team.abbrev} {odds.spread?.closing > 0 ? '+' : ''}{odds.spread?.closing || 'N/A'}
              </p>
              {odds.spread?.movement && (
                <p className={cn(
                  "text-xs mt-1",
                  odds.spread.movement > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {odds.spread.movement > 0 ? '↑' : '↓'} {Math.abs(odds.spread.movement)}
                </p>
              )}
            </div>
            
            {/* Total */}
            <div className="text-center p-3 bg-dark-800 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">Total</p>
              <p className="text-sm font-semibold text-white">
                O/U {odds.total?.closing || 'N/A'}
              </p>
              {odds.total?.movement && (
                <p className={cn(
                  "text-xs mt-1",
                  odds.total.movement > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {odds.total.movement > 0 ? '↑' : '↓'} {Math.abs(odds.total.movement)}
                </p>
              )}
            </div>
            
            {/* Moneyline */}
            <div className="text-center p-3 bg-dark-800 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">ML</p>
              <p className="text-sm font-semibold text-white">
                {odds.moneyline?.home || 'N/A'}
              </p>
            </div>
          </div>
          
          <Link to={`/games/${game_id}`}>
            <Button variant="ghost" size="sm" className="w-full">
              <TrendingUp className="w-4 h-4 mr-2" />
              Compare Books & View Movement
            </Button>
          </Link>
        </div>
      )}
      
      {/* Weather Section (Outdoor Games Only) */}
      {showWeather && hasWeather && (
        <div className="border-t border-dark-700 pt-4 mt-4">
          {/* Weather Badge */}
          <div className="mb-3">
            <WeatherBadge
              severity={weatherSeverity}
              temp_f={weather.temp_f}
              wind_mph={weather.wind_mph}
              precip_prob={weather.precip_prob}
              is_cold={weather.flags?.cold}
              is_windy={weather.flags?.windy}
              is_heavy_wind={weather.flags?.heavy_wind}
              is_rain_risk={weather.flags?.rain_risk}
              is_storm_risk={weather.flags?.storm_risk}
              size="sm"
            />
          </div>
          
          {/* Quick Weather Stats */}
          <div className="flex items-center gap-4 text-xs text-slate-400 mb-3">
            {weather.temp_f && (
              <span>🌡️ {weather.temp_f}°F</span>
            )}
            {weather.wind_mph && (
              <span>💨 {weather.wind_mph} mph</span>
            )}
            {weather.precip_prob > 0 && (
              <span>🌧️ {weather.precip_prob}% precip</span>
            )}
          </div>
          
          {/* Expandable Details */}
          <button
            onClick={() => setWeatherExpanded(!weatherExpanded)}
            className="flex items-center justify-between w-full p-2 hover:bg-dark-800 rounded-lg transition-colors text-sm text-slate-400 hover:text-white"
          >
            <span>More Weather Details</span>
            {weatherExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          
          {weatherExpanded && (
            <div className="mt-3 p-4 bg-dark-800 rounded-lg space-y-2 text-sm animate-slide-down">
              <div className="flex justify-between">
                <span className="text-slate-400">Source:</span>
                <span className="text-white">{weather.source || 'N/A'}</span>
              </div>
              {weather.temp_f && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Temperature:</span>
                  <span className="text-white">{weather.temp_f}°F</span>
                </div>
              )}
              {weather.wind_mph && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Wind Speed:</span>
                  <span className="text-white">{weather.wind_mph} mph</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-400">Severity Score:</span>
                <span className="text-white">{weatherSeverity} / 100</span>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Dome Message */}
      {showWeather && isDome && (
        <div className="border-t border-dark-700 pt-4 mt-4">
          <div className="p-3 bg-dark-800 rounded-lg text-center">
            <MapPin className="w-5 h-5 text-slate-500 mx-auto mb-2" />
            <p className="text-sm text-slate-400">
              Indoor game - weather not a factor
            </p>
          </div>
        </div>
      )}
      
      {/* View Details */}
      <div className="border-t border-dark-700 pt-4 mt-4">
        <Link to={`/games/${game_id}`}>
          <Button variant="primary" size="md" className="w-full">
            View Full Game Details
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>
      </div>
    </Card>
  );
};

export default GameCard;
