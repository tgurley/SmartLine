import { Trophy, TrendingUp, Cloud, Home } from 'lucide-react';
import Card from './Card';

/**
 * GamesSummary - Summary statistics for the week
 */
const GamesSummary = ({ games = [] }) => {
  
  // Calculate stats
  const totalGames = games.length;
  
  const completedGames = games.filter(g => g.result);
  const avgScore = completedGames.length > 0
    ? (completedGames.reduce((sum, g) => sum + g.result.home_score + g.result.away_score, 0) / completedGames.length).toFixed(1)
    : 'N/A';
  
  const outdoorGames = games.filter(g => !g.venue?.is_dome).length;
  const domeGames = games.filter(g => g.venue?.is_dome).length;
  
  const severeWeatherGames = games.filter(g => 
    !g.venue?.is_dome && g.weather?.severity_score >= 3
  ).length;
  
  const stats = [
    {
      label: 'Total Games',
      value: totalGames,
      icon: Trophy,
      color: 'primary',
      subtext: `${completedGames.length} completed`
    },
    {
      label: 'Avg Total Points',
      value: avgScore,
      icon: TrendingUp,
      color: 'violet',
      subtext: completedGames.length > 0 ? `${completedGames.length} games` : 'No results yet'
    },
    {
      label: 'Venue Split',
      value: `${outdoorGames}/${domeGames}`,
      icon: Cloud,
      color: 'emerald',
      subtext: 'Outdoor / Dome'
    },
    {
      label: 'Severe Weather',
      value: severeWeatherGames,
      icon: Home,
      color: 'amber',
      subtext: severeWeatherGames > 0 ? 'Games affected' : 'No severe weather'
    },
  ];
  
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        
        return (
          <Card 
            key={index}
            variant="glass" 
            padding="md"
            className="animate-slide-up"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
                <p className="text-3xl font-display font-bold text-white mb-1">
                  {stat.value}
                </p>
                <p className="text-xs text-slate-500">{stat.subtext}</p>
              </div>
              <div className={`w-12 h-12 bg-${stat.color}-500/10 rounded-lg flex items-center justify-center`}>
                <Icon className={`w-6 h-6 text-${stat.color}-400`} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default GamesSummary;
