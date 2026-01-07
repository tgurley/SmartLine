import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Search, 
  Bell, 
  User, 
  Menu,
  X,
  Loader2,
  Users
} from 'lucide-react';
import Button from '../ui/Button';
import AlertCenter from '../bankroll/alerts/AlertCenter';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';

const Header = ({ onMenuClick }) => {
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [playerResults, setPlayerResults] = useState([]);
  const [teamResults, setTeamResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const mobileSearchRef = useRef(null);
  const navigate = useNavigate();
  const [showAlerts, setShowAlerts] = useState(false);
  const [unreadAlertCount, setUnreadAlertCount] = useState(0);
  const alertButtonRef = useRef(null);

  useEffect(() => {
    fetchUnreadCount();
    
    // Poll for new alerts every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    
    return () => clearInterval(interval);
  }, []);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target) &&
          mobileSearchRef.current && !mobileSearchRef.current.contains(event.target)) {
        setShowDropdown(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setPlayerResults([]);
      setTeamResults([]);
      setShowDropdown(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchAll(query);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const searchAll = async (searchQuery) => {
    try {
      setLoading(true);
      
      // Search both players and teams in parallel
      const [playersResponse, teamsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/players/search?q=${encodeURIComponent(searchQuery)}&limit=5`),
        fetch(`${API_BASE_URL}/teams/search?q=${encodeURIComponent(searchQuery)}&limit=5`)
      ]);
      
      const playersData = playersResponse.ok ? await playersResponse.json() : { results: [] };
      const teamsData = teamsResponse.ok ? await teamsResponse.json() : { results: [] };
      
      setPlayerResults(playersData.results || []);
      setTeamResults(teamsData.results || []);
      setShowDropdown(true);
      setSelectedIndex(-1);
    } catch (err) {
      console.error('Failed to search:', err);
      setPlayerResults([]);
      setTeamResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = (player) => {
    navigate(`/players/${player.player_id}`);
    clearSearch();
  };

  const handleTeamSelect = (team) => {
    navigate(`/teams/${team.team_id}`);
    clearSearch();
  };

  const clearSearch = () => {
    setQuery('');
    setPlayerResults([]);
    setTeamResults([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    setSearchOpen(false);
  };

  // Combine results for keyboard navigation
  const allResults = [
    ...teamResults.map(t => ({ type: 'team', data: t })),
    ...playerResults.map(p => ({ type: 'player', data: p }))
  ];

  const handleKeyDown = (e) => {
    if (!showDropdown || allResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < allResults.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < allResults.length) {
          const result = allResults[selectedIndex];
          if (result.type === 'team') {
            handleTeamSelect(result.data);
          } else {
            handlePlayerSelect(result.data);
          }
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const getPositionColor = (position) => {
    const colors = {
      'QB': 'text-purple-400',
      'RB': 'text-emerald-400',
      'WR': 'text-sky-400',
      'TE': 'text-amber-400',
      'OL': 'text-orange-400',
      'DL': 'text-red-400',
      'LB': 'text-rose-400',
      'DB': 'text-indigo-400',
      'CB': 'text-blue-400',
      'S': 'text-cyan-400',
      'K': 'text-violet-400',
      'P': 'text-fuchsia-400',
    };
    return colors[position] || 'text-slate-400';
  };

  const SearchDropdown = ({ containerRef }) => {
    if (!showDropdown) return null;

    const hasResults = teamResults.length > 0 || playerResults.length > 0;

    if (!hasResults && !loading && query.trim()) {
      return (
        <div 
          ref={containerRef}
          className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 p-8 text-center z-50"
        >
          <Search className="w-12 h-12 mx-auto mb-3 text-slate-600" />
          <p className="text-slate-400 mb-1">No results found</p>
          <p className="text-sm text-slate-600">Try a different search term</p>
        </div>
      );
    }

    if (!hasResults) return null;

    let currentIndex = 0;

    return (
      <div 
        ref={containerRef}
        className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 max-h-96 overflow-y-auto z-50"
      >
        {/* Teams Section */}
        {teamResults.length > 0 && (
          <div>
            <div className="px-4 py-2 bg-dark-800/50 border-b border-dark-700">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Teams</span>
            </div>
            {teamResults.map((team) => {
              const itemIndex = currentIndex++;
              return (
                <button
                  key={`team-${team.team_id}`}
                  onClick={() => handleTeamSelect(team)}
                  className={`
                    w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-800 transition-colors text-left
                    ${itemIndex === selectedIndex ? 'bg-dark-800' : ''}
                    border-b border-dark-700
                  `}
                >
                  {/* Team Logo */}
                  {team.logo_url ? (
                    <img
                      src={team.logo_url}
                      alt={team.name}
                      className="w-10 h-10 rounded-lg object-contain bg-dark-800 border border-dark-700 p-1.5 flex-shrink-0"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextElementSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div 
                    className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center flex-shrink-0 border border-primary-500/30"
                    style={{ display: team.logo_url ? 'none' : 'flex' }}
                  >
                    <span className="text-white font-bold text-sm">{team.abbrev}</span>
                  </div>

                  {/* Team Info */}
                  <div className="flex-grow min-w-0">
                    <div className="font-semibold text-slate-200 truncate mb-1">
                      {team.name}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <span className="font-mono font-bold text-primary-400">{team.abbrev}</span>
                      {team.city && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span>{team.city}</span>
                        </>
                      )}
                      {team.player_count > 0 && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span>{team.player_count} players</span>
                        </>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Players Section */}
        {playerResults.length > 0 && (
          <div>
            <div className="px-4 py-2 bg-dark-800/50 border-b border-dark-700">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Players</span>
            </div>
            {playerResults.map((player) => {
              const itemIndex = currentIndex++;
              return (
                <button
                  key={`player-${player.player_id}`}
                  onClick={() => handlePlayerSelect(player)}
                  className={`
                    w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-800 transition-colors text-left
                    ${itemIndex === selectedIndex ? 'bg-dark-800' : ''}
                    ${itemIndex !== allResults.length - 1 ? 'border-b border-dark-700' : ''}
                  `}
                >
                  {/* Player Image */}
                  {player.image_url ? (
                    <img
                      src={player.image_url}
                      alt={player.full_name}
                      className="w-10 h-10 rounded-lg object-cover border border-dark-700 flex-shrink-0"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-lg bg-dark-800 border border-dark-700 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-slate-600" />
                    </div>
                  )}

                  {/* Player Info */}
                  <div className="flex-grow min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-slate-200 truncate">
                        {player.full_name}
                      </span>
                      {player.jersey_number && (
                        <span className="text-xs font-mono font-bold text-primary-400 bg-primary-500/10 px-1.5 py-0.5 rounded border border-primary-500/30 flex-shrink-0">
                          #{player.jersey_number}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      {player.position && (
                        <span className={`font-mono font-bold ${getPositionColor(player.position)}`}>
                          {player.position}
                        </span>
                      )}
                      {player.team_abbrev && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-400">{player.team_abbrev}</span>
                        </>
                      )}
                      {player.college && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-500 truncate">{player.college}</span>
                        </>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/bankroll/alerts/unread-count?user_id=1`);
      const data = await response.json();
      setUnreadAlertCount(data.count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };
  
  return (
    <header className="sticky top-0 z-50 bg-dark-950/95 backdrop-blur-sm border-b border-dark-700">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Left: Mobile menu + Logo */}
          <div className="flex items-center gap-4">
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">SL</span>
              </div>
              <span className="font-display font-bold text-xl text-white hidden sm:block">
                SmartLine
              </span>
            </Link>
          </div>
          
          {/* Center: Search (Desktop) */}
          <div className="hidden md:flex flex-1 max-w-lg mx-8">
            <div ref={searchRef} className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 pointer-events-none z-10" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => query.trim() && setShowDropdown(true)}
                placeholder="Search games, teams, or players..."
                className="w-full pl-10 pr-10 py-2 bg-dark-900 border border-dark-700 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
              {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
                </div>
              )}
              {query && !loading && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              
              <SearchDropdown />
            </div>
          </div>
          
          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Mobile Search Toggle */}
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="md:hidden p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
              aria-label="Search"
            >
              <Search className="w-5 h-5" />
            </button>
            
            {/* Notifications */}
            <div className="relative">
              <button
                ref={alertButtonRef}
                onClick={() => setShowAlerts(!showAlerts)}
                className="relative p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
                aria-label="Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadAlertCount > 0 && (
                  <>
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                    <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">
                      {unreadAlertCount > 9 ? '9+' : unreadAlertCount}
                    </span>
                  </>
                )}
              </button>
              
              <AlertCenter
                isOpen={showAlerts}
                onClose={() => {
                  setShowAlerts(false);
                  fetchUnreadCount(); // Refresh count when closing
                }}
                triggerRef={alertButtonRef}
              />
            </div>
            
            {/* User Menu */}
            <button
              className="flex items-center gap-2 p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
              aria-label="User menu"
            >
              <User className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Mobile Search */}
        {searchOpen && (
          <div className="md:hidden pb-4 animate-slide-down">
            <div ref={mobileSearchRef} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 pointer-events-none z-10" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => query.trim() && setShowDropdown(true)}
                placeholder="Search..."
                className="w-full pl-10 pr-10 py-2 bg-dark-900 border border-dark-700 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
              />
              {loading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                  <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
                </div>
              )}
              {query && !loading && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              
              <SearchDropdown />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
