import { useState, useEffect } from 'react';
import { Snowflake, TrendingUp, ArrowRight, Target, Flame } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const FeaturedBetsSection = () => {
  const [featuredBets, setFeaturedBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState('all');

  const API_BASE = 'https://smartline-production.up.railway.app';

  const marketOptions = [
    { key: 'all', label: 'All Props' },
    { key: 'player_pass_yds', label: 'Pass Yds' },
    { key: 'player_rush_yds', label: 'Rush Yds' },
    { key: 'player_reception_yds', label: 'Rec Yds' },
    { key: 'player_pass_tds', label: 'Pass TDs' },
    { key: 'player_anytime_td', label: 'Anytime TD' },
  ];

  useEffect(() => {
    const fetchFeaturedBets = async () => {
      try {
        setLoading(true);
        
        // Fetch hot streaks for week 18, 2023
        const streaksResponse = await fetch(
          `${API_BASE}/player-odds/streaks?season_year=2023&min_streak_length=3&streak_type=over`
        );
        const streaks = await streaksResponse.json();

        // For each hot player, get their best odds
        const featuredPromises = streaks.slice(0, 6).map(async (streak) => {
          try {
            const bestOddsResponse = await fetch(
              `${API_BASE}/player-odds/best-odds?player_id=${streak.player_id}&market_key=${streak.market_key}&season_year=2023&week=18&bet_type=over&limit=1`
            );
            const bestOdds = await bestOddsResponse.json();
            
            return {
              ...streak,
              bestOdds: bestOdds[0] || null
            };
          } catch (error) {
            console.error('Error fetching best odds:', error);
            return { ...streak, bestOdds: null };
          }
        });

        const featured = await Promise.all(featuredPromises);
        setFeaturedBets(featured.filter(bet => bet.bestOdds));
        
      } catch (error) {
        console.error('Error fetching featured bets:', error);
        setFeaturedBets([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFeaturedBets();
  }, [selectedMarket]);

  const formatMarketKey = (key) => {
    const names = {
      'player_pass_yds': 'Pass Yds',
      'player_pass_tds': 'Pass TDs',
      'player_rush_yds': 'Rush Yds',
      'player_reception_yds': 'Rec Yds',
      'player_anytime_td': 'Anytime TD'
    };
    return names[key] || key;
  };

  const getPositionColor = (position) => {
    const colors = {
      'QB': 'from-red-500 to-orange-500',
      'RB': 'from-green-500 to-emerald-500',
      'WR': 'from-blue-500 to-cyan-500',
      'TE': 'from-purple-500 to-pink-500',
    };
    return colors[position] || 'from-slate-500 to-slate-600';
  };

  if (loading) {
    return (
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>
            <Flame className="w-5 h-5 text-orange-400 mr-2 inline" />
            Featured Hot Bets
          </Card.Title>
          <Card.Description>
            Loading trending props...
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-48 bg-dark-800 rounded-lg animate-pulse"></div>
            ))}
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 w-full">
          <div>
            <Card.Title className="flex items-center">
              <Flame className="w-5 h-5 text-orange-400 mr-2" />
              Featured Hot Bets
            </Card.Title>
            <Card.Description>
              Players on fire with 3+ game streaks hitting OVER
            </Card.Description>
          </div>
          
          {/* Market Filter */}
          <div className="flex gap-2 flex-wrap">
            {marketOptions.map((market) => (
              <button
                key={market.key}
                onClick={() => setSelectedMarket(market.key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  selectedMarket === market.key
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                    : 'bg-dark-800 text-slate-400 hover:bg-dark-700 hover:text-white'
                }`}
              >
                {market.label}
              </button>
            ))}
          </div>
        </div>
      </Card.Header>
      
      <Card.Content>
        {featuredBets.length === 0 ? (
          <div className="text-center py-12">
            <Snowflake className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No hot streaks found for this market</p>
            <p className="text-sm text-slate-500 mt-1">Try selecting a different prop type</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredBets.map((bet, index) => (
              <div
                key={`${bet.player_id}-${bet.market_key}`}
                className="group relative bg-dark-800 rounded-xl p-5 hover:bg-dark-700 transition-all cursor-pointer border border-dark-700 hover:border-orange-500/50 animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                {/* Streak Fire Indicator */}
                <div className="absolute top-3 right-3">
                  <div className="relative">
                    <Flame className="w-6 h-6 text-orange-400 animate-pulse" />
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                      {bet.current_streak_length}
                    </span>
                  </div>
                </div>

                {/* Player Info */}
                <div className="mb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${getPositionColor(bet.position)} flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
                      {bet.position}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-white font-semibold text-lg leading-tight group-hover:text-orange-400 transition-colors">
                        {bet.player_name}
                      </h3>
                      <p className="text-slate-400 text-sm">
                        {formatMarketKey(bet.market_key)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Streak Stats */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-dark-900 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Current Streak</p>
                    <p className="text-xl font-bold text-orange-400">
                      {bet.current_streak_length}
                      <span className="text-sm text-slate-400 ml-1">games</span>
                    </p>
                  </div>
                  <div className="bg-dark-900 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">Season Best</p>
                    <p className="text-xl font-bold text-emerald-400">
                      {bet.longest_over_streak}
                      <span className="text-sm text-slate-400 ml-1">games</span>
                    </p>
                  </div>
                </div>

                {/* Best Odds */}
                {bet.bestOdds && (
                  <div className="border-t border-dark-700 pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-500">Best Line (Week 18)</span>
                      <Badge variant="primary" size="sm">
                        {bet.bestOdds.best_odds_bookmaker}
                      </Badge>
                    </div>
                    <div className="flex items-baseline justify-between">
                      <div>
                        <span className="text-slate-400 text-sm">O/U </span>
                        <span className="text-white font-bold text-lg">
                          {bet.bestOdds.line_value}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-emerald-400 font-bold text-lg">
                          {bet.bestOdds.best_odds_american > 0 ? '+' : ''}
                          {bet.bestOdds.best_odds_american}
                        </div>
                        <div className="text-xs text-slate-500">
                          {((bet.bestOdds.best_odds_american > 0 
                            ? 100 / (bet.bestOdds.best_odds_american + 100) 
                            : Math.abs(bet.bestOdds.best_odds_american) / (Math.abs(bet.bestOdds.best_odds_american) + 100)) * 100).toFixed(1)}% implied
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Hover Effect */}
                <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <ArrowRight className="w-5 h-5 text-orange-400" />
                </div>
              </div>
            ))}
          </div>
        )}
      </Card.Content>
      
      <Card.Footer>
        <Button variant="ghost" size="sm">
          View all hot streaks
        </Button>
        <span className="text-sm text-slate-500">
          {featuredBets.length} players on fire
        </span>
      </Card.Footer>
    </Card>
  );
};

export default FeaturedBetsSection;
