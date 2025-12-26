import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const LineMovementSection = () => {
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMagnitude, setSelectedMagnitude] = useState('all');

  const API_BASE = 'https://smartline-production.up.railway.app';

  const magnitudeOptions = [
    { key: 'all', label: 'All Movement' },
    { key: 'major', label: 'Major (10+)', color: 'red' },
    { key: 'significant', label: 'Significant (5-10)', color: 'orange' },
    { key: 'moderate', label: 'Moderate (2-5)', color: 'yellow' },
  ];

  useEffect(() => {
    const fetchLineMovement = async () => {
      try {
        setLoading(true);
        
        // Fetch sharp line movements for 2023 season
        const url = selectedMagnitude === 'all'
          ? `${API_BASE}/player-odds/sharp-movement?season_year=2023&limit=50`
          : `${API_BASE}/player-odds/sharp-movement?season_year=2023&movement_magnitude=${selectedMagnitude}&limit=50`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Sort by absolute movement value
        const sorted = data.sort((a, b) => 
          Math.abs(b.line_movement) - Math.abs(a.line_movement)
        );
        
        setMovements(sorted.slice(0, 8)); // Show top 8
        
      } catch (error) {
        console.error('Error fetching line movements:', error);
        setMovements([]);
      } finally {
        setLoading(false);
      }
    };

    fetchLineMovement();
  }, [selectedMagnitude]);

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

  const getMagnitudeBadge = (magnitude) => {
    const config = {
      'major': { variant: 'error', label: 'Major' },
      'significant': { variant: 'warning', label: 'Significant' },
      'moderate': { variant: 'default', label: 'Moderate' },
      'minor': { variant: 'default', label: 'Minor' },
    };
    return config[magnitude] || config.minor;
  };

  if (loading) {
    return (
      <Card variant="elevated">
        <Card.Header>
          <Card.Title>
            <Activity className="w-5 h-5 text-blue-400 mr-2 inline" />
            Sharp Line Movement
          </Card.Title>
          <Card.Description>Loading movement data...</Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-dark-800 rounded-lg animate-pulse"></div>
            ))}
          </div>
        </Card.Content>
      </Card>
    );
  }

  return (
    <Card variant="elevated">
      <Card.Header>
        <div className="flex flex-col gap-4 w-full">
          <div>
            <Card.Title className="flex items-center">
              <Activity className="w-5 h-5 text-blue-400 mr-2" />
              Sharp Line Movement
            </Card.Title>
            <Card.Description>
              Significant prop line changes indicating sharp money
            </Card.Description>
          </div>
          
          {/* Magnitude Filter */}
          <div className="flex gap-2 flex-wrap">
            {magnitudeOptions.map((option) => (
              <button
                key={option.key}
                onClick={() => setSelectedMagnitude(option.key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  selectedMagnitude === option.key
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
                    : 'bg-dark-800 text-slate-400 hover:bg-dark-700 hover:text-white'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </Card.Header>
      
      <Card.Content>
        {movements.length === 0 ? (
          <div className="text-center py-8">
            <AlertCircle className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No line movements found</p>
            <p className="text-sm text-slate-500 mt-1">
              Note: Currently showing historical snapshot data
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {movements.map((movement, index) => {
              const isPositive = movement.line_movement > 0;
              const magnitudeBadge = getMagnitudeBadge(movement.movement_magnitude);
              
              return (
                <div
                  key={`${movement.game_id}-${movement.player_id}-${movement.market_key}`}
                  className="group flex items-center justify-between p-4 bg-dark-800 rounded-lg hover:bg-dark-700 transition-all cursor-pointer border border-dark-700 hover:border-blue-500/50 animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Left Side - Player Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-2 rounded-lg ${isPositive ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
                        {isPositive ? (
                          <TrendingUp className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-white font-semibold truncate group-hover:text-blue-400 transition-colors">
                          {movement.player_name}
                        </h4>
                        <p className="text-sm text-slate-400">
                          {formatMarketKey(movement.market_key)} • {movement.bet_type.toUpperCase()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Middle - Line Movement */}
                  <div className="flex items-center gap-4 mx-4">
                    <div className="text-center">
                      <p className="text-xs text-slate-500 mb-1">Opening</p>
                      <p className="text-white font-mono font-semibold">
                        {movement.opening_line}
                      </p>
                    </div>
                    
                    <div className="flex flex-col items-center">
                      {isPositive ? (
                        <TrendingUp className="w-5 h-5 text-emerald-400 mb-1" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-red-400 mb-1" />
                      )}
                      <Badge 
                        variant={isPositive ? 'success' : 'error'} 
                        size="md"
                        className="font-mono font-bold"
                      >
                        {isPositive ? '+' : ''}{movement.line_movement}
                      </Badge>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-xs text-slate-500 mb-1">Current</p>
                      <p className="text-white font-mono font-semibold">
                        {movement.current_line}
                      </p>
                    </div>
                  </div>

                  {/* Right Side - Magnitude Badge */}
                  <div className="flex items-center gap-3">
                    <Badge variant={magnitudeBadge.variant} size="md">
                      {magnitudeBadge.label}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card.Content>
      
      <Card.Footer>
        <Button variant="ghost" size="sm">
          View all movements
        </Button>
        <span className="text-sm text-slate-500">
          {movements.length} sharp movements detected
        </span>
      </Card.Footer>

      {/* Info Banner */}
      <div className="mx-6 mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-blue-300 font-medium mb-1">
              Historical Data Notice
            </p>
            <p className="text-xs text-blue-400/80">
              Currently showing line movements from historical data (single snapshot). 
              Real-time movement tracking will be available when live odds integration is complete.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default LineMovementSection;
