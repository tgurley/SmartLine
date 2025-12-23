import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const Dashboard = () => {
  // Sample data - will be replaced with real data later
  const stats = [
    {
      label: 'Total Games Tracked',
      value: '272',
      change: '+12%',
      trend: 'up',
      icon: Activity,
      color: 'primary'
    },
    {
      label: 'Avg Line Movement',
      value: '2.3 pts',
      change: '+0.4',
      trend: 'up',
      icon: TrendingUp,
      color: 'emerald'
    },
    {
      label: 'Books Monitored',
      value: '4',
      change: 'All active',
      trend: 'neutral',
      icon: DollarSign,
      color: 'violet'
    },
    {
      label: 'Sharp Money Alerts',
      value: '18',
      change: '6 new',
      trend: 'down',
      icon: TrendingDown,
      color: 'amber'
    },
  ];
  
  const recentGames = [
    { away: 'KC', home: 'BUF', spread: -2.5, total: 48.5, movement: '+1.5', week: 6 },
    { away: 'SF', home: 'DAL', spread: -3.5, total: 45.5, movement: '-0.5', week: 5 },
    { away: 'PHI', home: 'MIA', spread: -1.5, total: 51.5, movement: '+2.0', week: 7 },
    { away: 'BAL', home: 'CIN', spread: -4.5, total: 47.5, movement: '-1.0', week: 5 },
  ];
  
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Dashboard
          </h1>
          <p className="text-slate-400">
            Welcome back! Here's your NFL betting analytics overview
          </p>
        </div>
        <Button variant="primary" size="md">
          View All Games
        </Button>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card 
              key={index} 
              variant="glass" 
              hover 
              className="animate-slide-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 bg-${stat.color}-500/10 rounded-lg flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-400`} />
                </div>
                {stat.trend === 'up' && (
                  <Badge variant="success" size="sm">
                    {stat.change}
                  </Badge>
                )}
                {stat.trend === 'down' && (
                  <Badge variant="warning" size="sm">
                    {stat.change}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
              <p className="text-2xl font-display font-bold text-white">
                {stat.value}
              </p>
            </Card>
          );
        })}
      </div>
      
      {/* Recent Games */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Games with Line Movement */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>Significant Line Movement</Card.Title>
            <Card.Description>
              Games with major spread changes
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-3">
              {recentGames.map((game, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-dark-800 rounded-lg hover:bg-dark-700 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-sm">
                      <Badge variant="default" size="sm">Week {game.week}</Badge>
                    </div>
                    <div>
                      <p className="text-white font-medium">
                        {game.away} @ {game.home}
                      </p>
                      <p className="text-sm text-slate-400">
                        {game.home} {game.spread} | O/U {game.total}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant={game.movement.startsWith('+') ? 'success' : 'error'}
                    size="md"
                  >
                    {game.movement}
                  </Badge>
                </div>
              ))}
            </div>
          </Card.Content>
          <Card.Footer>
            <Button variant="ghost" size="sm">
              View all games
            </Button>
            <span className="text-sm text-slate-500">
              4 of 272 games
            </span>
          </Card.Footer>
        </Card>
        
        {/* Quick Actions */}
        <Card variant="elevated">
          <Card.Header>
            <Card.Title>Quick Actions</Card.Title>
            <Card.Description>
              Common tasks and shortcuts
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-3">
              <Button variant="outline" className="w-full justify-start" size="md">
                <TrendingUp className="w-5 h-5 mr-2" />
                Compare Sportsbooks
              </Button>
              <Button variant="outline" className="w-full justify-start" size="md">
                <Activity className="w-5 h-5 mr-2" />
                View Line Movements
              </Button>
              <Button variant="outline" className="w-full justify-start" size="md">
                <DollarSign className="w-5 h-5 mr-2" />
                Best Odds Finder
              </Button>
            </div>
          </Card.Content>
          <Card.Footer>
            <p className="text-sm text-slate-500">
              More features coming soon
            </p>
          </Card.Footer>
        </Card>
      </div>
      
      {/* Placeholder for Charts */}
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>Weekly Trends</Card.Title>
          <Card.Description>
            Line movement patterns across the season
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="h-64 flex items-center justify-center bg-dark-900 rounded-lg border-2 border-dashed border-dark-700">
            <p className="text-slate-500">Chart visualization coming soon</p>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default Dashboard;
