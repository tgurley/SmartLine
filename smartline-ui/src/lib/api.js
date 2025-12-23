/**
 * API Configuration for SmartLine
 * Update VITE_API_URL in your .env files
 */

// Your Railway backend URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "smartline-production.up.railway.app";

/**
 * Games API endpoints (already working)
 */
export const gamesAPI = {
  // Get all games for a week
  getGames: (season, week) => 
    `${API_BASE_URL}/games?season=${season}&week=${week}`,
  
  // Get specific game details
  getGame: (gameId) => 
    `${API_BASE_URL}/games/${gameId}`,
};

/**
 * Weather API endpoints (integrated with your existing /games endpoint)
 */
export const weatherAPI = {
  // Weather is already included in /games endpoint
  // But we can add dedicated endpoints if needed
  
  // For now, use games endpoint and extract weather
  getGamesWithWeather: (season, week) => 
    `${API_BASE_URL}/games?season=${season}&week=${week}`,
};

/**
 * Odds API endpoints (NEW - add these to your main.py)
 */
export const oddsAPI = {
  // Get odds for games
  getOdds: (season, week = null, gameId = null) => {
    const params = new URLSearchParams({ season: season.toString() });
    if (week) params.append('week', week.toString());
    if (gameId) params.append('game_id', gameId.toString());
    return `${API_BASE_URL}/odds?${params}`;
  },
  
  // Get all odds for specific game
  getGameOdds: (gameId) => 
    `${API_BASE_URL}/odds/game/${gameId}`,
  
  // Get line movement analysis
  getLineMovement: (season, week = null, market = 'spread') => {
    const params = new URLSearchParams({ 
      season: season.toString(),
      market 
    });
    if (week) params.append('week', week.toString());
    return `${API_BASE_URL}/odds/movement?${params}`;
  },
  
  // Compare odds across books
  compareOdds: (gameId, market = 'spread') =>
    `${API_BASE_URL}/odds/compare?game_id=${gameId}&market=${market}`,
};

/**
 * Fetch wrapper with error handling
 */
export const apiFetch = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

/**
 * Helper to extract weather from games response
 */
export const extractWeatherFromGames = (gamesResponse) => {
  return gamesResponse.games.map(game => ({
    game_id: game.game_id,
    week: gamesResponse.week,
    game_datetime_utc: game.kickoff_utc,
    away_team: game.away_team,
    home_team: game.home_team,
    venue: game.venue,
    weather: {
      temp_f: game.weather?.temp_f,
      temp_c: game.weather?.temp_f ? ((game.weather.temp_f - 32) * 5/9).toFixed(1) : null,
      wind_mph: game.weather?.wind_mph,
      precip_prob: game.weather?.precip_prob,
      precip_mm: game.weather?.precip_mm,
      weather_severity_score: game.weather?.severity_score || 0,
      is_cold: game.weather?.flags?.cold,
      is_hot: game.weather?.flags?.hot, // Add if you have this flag
      is_windy: game.weather?.flags?.windy,
      is_heavy_wind: game.weather?.flags?.heavy_wind,
      is_rain_risk: game.weather?.flags?.rain_risk,
      is_storm_risk: game.weather?.flags?.storm_risk,
      source: game.weather?.source,
    },
    result: game.result
  }));
};