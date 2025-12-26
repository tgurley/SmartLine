import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Target, Search, Zap, Flame, Snowflake, ArrowRight, Filter } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import FeaturedBetsSection from '../components/odds/FeaturedBetsSection';
import LineMovementSection from '../components/odds/LineMovementSection';
import LineShoppingTool from '../components/odds/LineShoppingTool';
import EndpointDiagnostics from '../components/odds/EndpointDiagnostics';

const OddsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [statsData, setStatsData] = useState(null);

  const API_BASE = 'https://smartline-production.up.railway.app';

  // Fetch overview stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch games with props for week 18, 2023
        const gamesResponse = await fetch(`${API_BASE}/player-odds/games?season_year=2023&week=18`);
        const games = await gamesResponse.json();

        // Fetch bookmaker stats
        const bookmakersResponse = await fetch(`${API_BASE}/player-odds/bookmakers?season_year=2023`);
        const bookmakers = await bookmakersResponse.json();

        setStatsData({
          gamesTracked: games.length || 0,
          totalProps: games.reduce((sum, game) => sum + (game.total_prop_count || 0), 0),
          booksMonitored: bookmakers.length || 0,
          avgPlayersPerGame: Math.round(
            games.reduce((sum, game) => sum + (game.players_with_props || 0), 0) / (games.length || 1)
          )
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
        setStatsData({
          gamesTracked: 0,
          totalProps: 0,
          booksMonitored: 0,
          avgPlayersPerGame: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const stats = [
    {
      label: 'Week 18 Games',
      value: loading ? '...' : statsData?.gamesTracked || '0',
      subtitle: '2023 Season',
      icon: Target,
      color: 'primary',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Player Props',
      value: loading ? '...' : statsData?.totalProps || '0',
      subtitle: 'Total markets',
      icon: Zap,
      color: 'emerald',
      gradient: 'from-emerald-500 to-teal-500'
    },
    {
      label: 'Sportsbooks',
      value: loading ? '...' : statsData?.booksMonitored || '0',
      subtitle: 'Monitored',
      icon: TrendingUp,
      color: 'violet',
      gradient: 'from-violet-500 to-purple-500'
    },
    {
      label: 'Avg Players/Game',
      value: loading ? '...' : statsData?.avgPlayersPerGame || '0',
      subtitle: 'With props',
      icon: Flame,
      color: 'amber',
      gradient: 'from-amber-500 to-orange-500'
    },
  ];

  return (
    <div className="space-y-8 pb-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Target className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-display font-bold text-white">
              Player Props Odds
            </h1>
          </div>
          <p className="text-slate-400">
            Live betting intelligence and line shopping for NFL player props
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="md">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          <Button variant="primary" size="md">
            <Search className="w-4 h-4 mr-2" />
            Find Best Odds
          </Button>
        </div>
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
              className="animate-slide-up overflow-hidden"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="relative">
                {/* Gradient background */}
                <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.gradient} opacity-10 rounded-full blur-2xl -mr-8 -mt-8`}></div>
                
                <div className="relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-12 h-12 bg-gradient-to-br ${stat.gradient} rounded-lg flex items-center justify-center shadow-lg`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
                  <p className="text-3xl font-display font-bold text-white mb-1">
                    {stat.value}
                  </p>
                  <p className="text-xs text-slate-500">{stat.subtitle}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Featured Bets - Hot Players/Teams */}
      <FeaturedBetsSection />

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Line Movement Section */}
        {/* <LineMovementSection /> */}

        {/* Line Shopping Tool */}
        <div className="lg:col-span-2">
          <LineShoppingTool />
        </div>
      </div>

      <EndpointDiagnostics />

      {/* Coming Soon Teaser */}
      <Card variant="elevated" className="border border-dashed border-slate-700">
        <Card.Content className="py-12">
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-display font-bold text-white mb-2">
              Live Odds Updates Coming Soon
            </h3>
            <p className="text-slate-400 mb-6">
              Real-time line movement tracking, sharp money alerts, and AI-powered betting insights will be available when live odds integration is complete.
            </p>
            <div className="flex justify-center gap-3">
              <Badge variant="primary" size="lg">
                <Flame className="w-4 h-4 mr-1" />
                In Development
              </Badge>
            </div>
          </div>
        </Card.Content>
      </Card>
    </div>
  );
};

export default OddsDashboard;
