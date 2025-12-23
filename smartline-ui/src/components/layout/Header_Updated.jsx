import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Search, 
  Bell, 
  User, 
  Menu,
  X,
  Loader2
} from 'lucide-react';
import Button from '../ui/Button';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';

const Header = ({ onMenuClick }) => {
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const mobileSearchRef = useRef(null);
  const navigate = useNavigate();
  
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
      setResults([]);
      setShowDropdown(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchPlayers(query);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const searchPlayers = async (searchQuery) => {
    try {
      setLoading(true);
      
      const response = await fetch(
        `${API_BASE_URL}/players/search?q=${encodeURIComponent(searchQuery)}&limit=8`
      );
      
      if (!response.ok) {
        throw new Error('Search failed');
      }
      
      const data = await response.json();
      setResults(data.results || []);
      setShowDropdown(true);
      setSelectedIndex(-1);
    } catch (err) {
      console.error('Failed to search players:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = (player) => {
    navigate(`/players/${player.player_id}`);
    setQuery('');
    setResults([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    setSearchOpen(false); // Close mobile search
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handlePlayerSelect(results[selectedIndex]);
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

  const PlayerDropdown = ({ results, onSelect, selectedIndex, containerRef }) => {
    if (!showDropdown || results.length === 0) {
      if (showDropdown && !loading && query.trim()) {
        return (
          <div 
            ref={containerRef}
            className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 p-8 text-center z-50"
          >
            <User className="w-12 h-12 mx-auto mb-3 text-slate-600" />
            <p className="text-slate-400 mb-1">No players found</p>
            <p className="text-sm text-slate-600">Try a different search term</p>
          </div>
        );
      }
      return null;
    }

    return (
      <div 
        ref={containerRef}
        className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 max-h-96 overflow-y-auto z-50"
      >
        {results.map((player, index) => (
          <button
            key={player.player_id}
            onClick={() => onSelect(player)}
            className={`
              w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-800 transition-colors text-left
              ${index === selectedIndex ? 'bg-dark-800' : ''}
              ${index !== results.length - 1 ? 'border-b border-dark-700' : ''}
            `}
          >
            {/* Player Image or Icon */}
            {player.image_url ? (
              <img
                src={player.image_url}
                alt={player.full_name}
                className="w-10 h-10 rounded-lg object-cover border border-dark-700 flex-shrink-0"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.style.display = 'none';
                  e.target.nextElementSibling.style.display = 'flex';
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
        ))}
      </div>
    );
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
                  onClick={() => {
                    setQuery('');
                    setResults([]);
                    setShowDropdown(false);
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              
              {/* Dropdown for Desktop */}
              <PlayerDropdown 
                results={results}
                onSelect={handlePlayerSelect}
                selectedIndex={selectedIndex}
              />
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
            <button
              className="relative p-2 text-slate-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            
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
                  onClick={() => {
                    setQuery('');
                    setResults([]);
                    setShowDropdown(false);
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
              
              {/* Dropdown for Mobile */}
              <PlayerDropdown 
                results={results}
                onSelect={handlePlayerSelect}
                selectedIndex={selectedIndex}
              />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
