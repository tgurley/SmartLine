import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, MapPin, Trophy } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { cn } from '../lib/utils';

// Import tab components
import GameOverview from '../components/game-detail/GameOverview';
import OddsMovement from '../components/game-detail/OddsMovement';
import WeatherDetail from '../components/game-detail/WeatherDetail';
import PlayerLines from '../components/game-detail/PlayerLines';

const GameDetailPage = () => {
  const { gameId } = useParams();
  const [activeTab, setActiveTab] = useState('overview');
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch game details
  useEffect(() => {
    const fetchGameDetail = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';
        const response = await fetch(`${apiUrl}/games/${gameId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch game details');
        }
        
        const data = await response.json();
        setGame(data);
      } catch (err) {
        console.error('Error fetching game:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGameDetail();
  }, [gameId]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading game details...</p>
        </div>
      </div>
    );
  }
  
  if (error || !game) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
          <p className="text-red-400 mb-4">Failed to load game details</p>
          <Link to="/games">
            <Button variant="outline">Back to Games</Button>
          </Link>
        </div>
      </div>
    );
  }
  
  const gameDate = new Date(game.kickoff_utc);
  const isFinal = game.status === 'final' || game.result !== null;
  const isDome = game.venue?.is_dome;
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Trophy },
    { id: 'odds', label: 'Odds Movement', icon: null },
    { id: 'weather', label: 'Weather Details', icon: null, disabled: isDome },
    { id: 'players', label: 'Player Lines', icon: null, badge: 'Soon' },
  ];
  
  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link to="/games">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Games
        </Button>
      </Link>
      
      {/* Game Header */}
      <Card variant="elevated" padding="lg" glow>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex-1">
            {/* Status Badges */}
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              {isFinal && (
                <Badge variant="success" size="md">Final</Badge>
              )}
              {isDome && (
                <Badge variant="default" size="md">
                  <MapPin className="w-3 h-3 mr-1" />
                  Dome
                </Badge>
              )}
            </div>
            
            {/* Teams */}
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-display font-bold text-white">
                    {game.away_team.abbrev}
                  </span>
                  <span className="text-slate-400">{game.away_team.name}</span>
                </div>
                {game.result && (
                  <span className="text-3xl font-bold text-white">
                    {game.result.away_score}
                  </span>
                )}
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-display font-bold text-white">
                    {game.home_team.abbrev}
                  </span>
                  <span className="text-slate-400">{game.home_team.name}</span>
                </div>
                {game.result && (
                  <span className="text-3xl font-bold text-white">
                    {game.result.home_score}
                  </span>
                )}
              </div>
            </div>
            
            {/* Game Info */}
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {gameDate.toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  month: 'long', 
                  day: 'numeric',
                  year: 'numeric'
                })}
              </span>
              <span>
                {gameDate.toLocaleTimeString('en-US', { 
                  hour: 'numeric', 
                  minute: '2-digit'
                })}
              </span>
            </div>
          </div>
        </div>
      </Card>
      
      {/* Tabs */}
      <div className="border-b border-dark-700">
        <div className="flex gap-1 overflow-x-auto scrollbar-hide">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isDisabled = tab.disabled;
            
            return (
              <button
                key={tab.id}
                onClick={() => !isDisabled && setActiveTab(tab.id)}
                disabled={isDisabled}
                className={cn(
                  "flex items-center gap-2 px-6 py-3 font-medium transition-all whitespace-nowrap",
                  "border-b-2 -mb-px",
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-400"
                    : "border-transparent text-slate-400 hover:text-white",
                  isDisabled && "opacity-50 cursor-not-allowed"
                )}
              >
                {Icon && <Icon className="w-4 h-4" />}
                {tab.label}
                {tab.badge && (
                  <Badge variant="primary" size="sm">{tab.badge}</Badge>
                )}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'overview' && <GameOverview game={game} />}
        {activeTab === 'odds' && <OddsMovement gameId={gameId} game={game} />}
        {activeTab === 'weather' && <WeatherDetail game={game} />}
        {activeTab === 'players' && <PlayerLines gameId={gameId} />}
      </div>
    </div>
  );
};

export default GameDetailPage;
