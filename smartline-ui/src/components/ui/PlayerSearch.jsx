// src/components/ui/PlayerSearch.jsx
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, User, X, Loader2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://smartline-production.up.railway.app';

export default function PlayerSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
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
      setIsOpen(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchPlayers(query);
    }, 300); // 300ms debounce

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
      setIsOpen(true);
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
    setIsOpen(false);
    setSelectedIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;

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
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
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

  return (
    <div ref={searchRef} className="relative w-full max-w-xl">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.trim() && setIsOpen(true)}
          placeholder="Search players..."
          className="w-full pl-10 pr-10 py-2 bg-dark-800 border border-dark-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Loader2 className="w-4 h-4 text-primary-400 animate-spin" />
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 max-h-96 overflow-y-auto z-50">
          {results.map((player, index) => (
            <button
              key={player.player_id}
              onClick={() => handlePlayerSelect(player)}
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
      )}

      {/* No Results */}
      {isOpen && !loading && query.trim() && results.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl shadow-black/50 p-8 text-center z-50">
          <User className="w-12 h-12 mx-auto mb-3 text-slate-600" />
          <p className="text-slate-400 mb-1">No players found</p>
          <p className="text-sm text-slate-600">Try a different search term</p>
        </div>
      )}
    </div>
  );
}
