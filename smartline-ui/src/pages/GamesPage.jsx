import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import WeekSelector from '../components/ui/WeekSelector';
import GameFilters from '../components/ui/GameFilters';
import GamesSummary from '../components/ui/GamesSummary';
import GameCard from '../components/ui/GameCard';

const GamesPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const season = Number(searchParams.get('season')) || 2023;
  const week = Number(searchParams.get('week')) || 1;
  const filter = searchParams.get('filter') || 'all';
  
  const [games, setGames] = useState([]);
  const [oddsData, setOddsData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch games data
  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';
        
        // Fetch games
        const gamesResponse = await fetch(`${apiUrl}/games?season=${season}&week=${week}`);
        if (!gamesResponse.ok) {
          throw new Error('Failed to fetch games');
        }
        const gamesData = await gamesResponse.json();
        setGames(gamesData.games || []);
        
        // Fetch odds for the week
        try {
          const oddsResponse = await fetch(`${apiUrl}/odds?season=${season}&week=${week}`);
          if (oddsResponse.ok) {
            const oddsResult = await oddsResponse.json();
            
            // Transform odds data into a map by game_id for easy lookup
            const oddsMap = {};
            if (oddsResult.games) {
              oddsResult.games.forEach(gameOdds => {
                // Get consensus/latest odds from all books
                const books = gameOdds.books || {};
                const bookNames = Object.keys(books);
                
                if (bookNames.length > 0) {
                  // Calculate consensus from all books
                  const spreadLines = [];
                  const totalLines = [];
                  const moneylines = [];
                  
                  bookNames.forEach(bookName => {
                    const book = books[bookName];
                    
                    // Get closing/latest lines
                    if (book.spread?.closing) {
                      spreadLines.push({
                        line: parseFloat(book.spread.closing.line),
                        price: book.spread.closing.price
                      });
                    }
                    if (book.total?.closing) {
                      totalLines.push({
                        line: parseFloat(book.total.closing.line),
                        price: book.total.closing.price
                      });
                    }
                    if (book.moneyline?.closing) {
                      moneylines.push({
                        home: book.moneyline.closing.home,
                        away: book.moneyline.closing.away
                      });
                    }
                  });
                  
                  // Calculate consensus and movement
                  oddsMap[gameOdds.game_id] = {
                    spread: {
                      closing: spreadLines.length > 0 
                        ? (spreadLines.reduce((sum, l) => sum + l.line, 0) / spreadLines.length).toFixed(1)
                        : null,
                      movement: null // Can calculate if we have opening lines
                    },
                    total: {
                      closing: totalLines.length > 0
                        ? (totalLines.reduce((sum, l) => sum + l.line, 0) / totalLines.length).toFixed(1)
                        : null,
                      movement: null
                    },
                    moneyline: {
                      home: moneylines.length > 0 ? moneylines[0].home : null,
                      away: moneylines.length > 0 ? moneylines[0].away : null
                    }
                  };
                }
              });
            }
            
            setOddsData(oddsMap);
          }
        } catch (oddsErr) {
          console.error('Error fetching odds:', oddsErr);
          // Don't fail the whole page if odds fail
        }
        
      } catch (err) {
        console.error('Error fetching games:', err);
        setError(err.message);
        setGames([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGames();
  }, [season, week]);
  
  // Filter games based on active filter
  const filteredGames = games.filter(game => {
    switch (filter) {
      case 'outdoor':
        return !game.venue?.is_dome;
      case 'dome':
        return game.venue?.is_dome;
      case 'severe':
        return !game.venue?.is_dome && (game.weather?.severity_score || 0) >= 3;
      case 'all':
      default:
        return true;
    }
  });
  
  // Calculate filter counts
  const filterCounts = {
    all: games.length,
    outdoor: games.filter(g => !g.venue?.is_dome).length,
    dome: games.filter(g => g.venue?.is_dome).length,
    severe: games.filter(g => !g.venue?.is_dome && (g.weather?.severity_score || 0) >= 3).length,
  };
  
  // Handlers
  const handleWeekChange = (newWeek) => {
    setSearchParams({ season: season.toString(), week: newWeek.toString(), filter });
  };
  
  const handleFilterChange = (newFilter) => {
    setSearchParams({ season: season.toString(), week: week.toString(), filter: newFilter });
  };
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div>
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Games
          </h1>
          <p className="text-slate-400">
            Week {week}, {season} NFL Season
          </p>
        </div>
        
        {/* Week Selector */}
        <WeekSelector
          currentWeek={week}
          onWeekChange={handleWeekChange}
          minWeek={1}
          maxWeek={18}
        />
      </div>
      
      {/* Summary Stats */}
      {!loading && !error && (
        <GamesSummary games={games} />
      )}
      
      {/* Filters */}
      <GameFilters
        activeFilter={filter}
        onFilterChange={handleFilterChange}
        counts={filterCounts}
      />
      
      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">Loading games...</p>
          </div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
          <p className="text-red-400 mb-2">Failed to load games</p>
          <p className="text-sm text-slate-400">{error}</p>
        </div>
      )}
      
      {/* Games Grid */}
      {!loading && !error && filteredGames.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredGames.map((game) => (
            <GameCard
              key={game.game_id}
              game={game}
              odds={oddsData[game.game_id] || null}
              showWeather={true}
              showOdds={true}
            />
          ))}
        </div>
      )}
      
      {/* No Games State */}
      {!loading && !error && filteredGames.length === 0 && games.length > 0 && (
        <div className="text-center py-20">
          <p className="text-slate-400 mb-4">No games match the selected filter</p>
          <button
            onClick={() => handleFilterChange('all')}
            className="text-primary-400 hover:text-primary-300 transition-colors"
          >
            View all games
          </button>
        </div>
      )}
      
      {/* No Games for Week */}
      {!loading && !error && games.length === 0 && (
        <div className="text-center py-20">
          <p className="text-slate-400">No games scheduled for this week</p>
        </div>
      )}
    </div>
  );
};

export default GamesPage;
