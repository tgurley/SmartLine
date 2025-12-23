import { Calendar, MapPin, Users, Trophy } from 'lucide-react';
import Card from '../ui/Card';
import WeatherBadge from '../ui/WeatherBadge';

/**
 * GameOverview - Overview tab showing game summary and quick stats
 */
const GameOverview = ({ game }) => {
  const isDome = game.venue?.is_dome;
  const hasWeather = game.weather && !isDome;
  const weatherSeverity = game.weather?.severity_score || 0;
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Game Information */}
      <Card variant="elevated" padding="lg">
        <Card.Header>
          <Card.Title>Game Information</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <Calendar className="w-5 h-5 text-primary-400 mt-0.5" />
              <div>
                <p className="text-sm text-slate-400">Date & Time</p>
                <p className="text-white font-medium">
                  {new Date(game.kickoff_utc).toLocaleString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-primary-400 mt-0.5" />
              <div>
                <p className="text-sm text-slate-400">Venue</p>
                <p className="text-white font-medium">
                  {game.venue?.name || 'TBD'}
                </p>
                <p className="text-xs text-slate-500">
                  {game.venue?.city}, {game.venue?.state}
                  {isDome && ' • Indoor'}
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <Trophy className="w-5 h-5 text-primary-400 mt-0.5" />
              <div>
                <p className="text-sm text-slate-400">Status</p>
                <p className="text-white font-medium">
                  {game.status === 'final' ? 'Final' : 'Scheduled'}
                </p>
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>
      
      {/* Weather Summary (Outdoor Games Only) */}
      {hasWeather && (
        <Card variant="elevated" padding="lg">
          <Card.Header>
            <Card.Title>Weather Conditions</Card.Title>
            <Card.Description>Current forecast for game time</Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="mb-4">
              <WeatherBadge
                severity={weatherSeverity}
                temp_f={game.weather.temp_f}
                wind_mph={game.weather.wind_mph}
                precip_prob={game.weather.precip_prob}
                is_cold={game.weather.flags?.cold}
                is_windy={game.weather.flags?.windy}
                is_heavy_wind={game.weather.flags?.heavy_wind}
                is_rain_risk={game.weather.flags?.rain_risk}
                is_storm_risk={game.weather.flags?.storm_risk}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400">Temperature</p>
                <p className="text-2xl font-bold text-white">
                  {game.weather.temp_f}°F
                </p>
              </div>
              
              <div>
                <p className="text-sm text-slate-400">Wind Speed</p>
                <p className="text-2xl font-bold text-white">
                  {game.weather.wind_mph} mph
                </p>
              </div>
              
              {game.weather.precip_prob > 0 && (
                <div className="col-span-2">
                  <p className="text-sm text-slate-400">Precipitation</p>
                  <p className="text-2xl font-bold text-white">
                    {game.weather.precip_prob}% chance
                  </p>
                </div>
              )}
            </div>
          </Card.Content>
        </Card>
      )}
      
      {/* Dome Message */}
      {isDome && (
        <Card variant="elevated" padding="lg">
          <Card.Content>
            <div className="text-center py-8">
              <MapPin className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-lg font-semibold text-white mb-2">Indoor Game</p>
              <p className="text-slate-400">
                This game will be played in a dome. Weather conditions are not a factor.
              </p>
            </div>
          </Card.Content>
        </Card>
      )}
      
      {/* Game Result (if completed) */}
      {game.result && (
        <Card variant="elevated" padding="lg" className="lg:col-span-2">
          <Card.Header>
            <Card.Title>Final Score</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="flex items-center justify-around py-4">
              <div className="text-center">
                <p className="text-sm text-slate-400 mb-2">{game.away_team.name}</p>
                <p className="text-5xl font-bold text-white">{game.result.away_score}</p>
              </div>
              
              <div className="text-3xl font-bold text-slate-600">-</div>
              
              <div className="text-center">
                <p className="text-sm text-slate-400 mb-2">{game.home_team.name}</p>
                <p className="text-5xl font-bold text-white">{game.result.home_score}</p>
              </div>
            </div>
            
            <div className="text-center mt-4 pt-4 border-t border-dark-700">
              <p className="text-sm text-slate-400">Total Points</p>
              <p className="text-2xl font-bold text-primary-400">
                {game.result.home_score + game.result.away_score}
              </p>
            </div>
          </Card.Content>
        </Card>
      )}
    </div>
  );
};

export default GameOverview;
