// src/constants/bettingMarkets.js
// Based on: https://the-odds-api.com/sports-odds-data/betting-markets.html

/**
 * BETTING MARKETS MAPPING
 * 
 * This file defines all available betting markets for different sports,
 * player positions, and teams. Used for filtering market options in bet entry.
 */

// =========================================================
// SPORT CONFIGURATIONS
// =========================================================

export const SPORTS = {
  NFL: {
    key: 'NFL',
    label: 'NFL',
    hasPlayers: true,
    hasTeams: true,
    icon: '🏈'
  },
  NBA: {
    key: 'NBA',
    label: 'NBA',
    hasPlayers: true,
    hasTeams: true,
    icon: '🏀'
  },
  MLB: {
    key: 'MLB',
    label: 'MLB',
    hasPlayers: true,
    hasTeams: true,
    icon: '⚾'
  },
  NHL: {
    key: 'NHL',
    label: 'NHL',
    hasPlayers: true,
    hasTeams: true,
    icon: '🏒'
  },
  NCAAF: {
    key: 'NCAAF',
    label: 'NCAAF',
    hasPlayers: true,
    hasTeams: true,
    icon: '🏈'
  },
  NCAAB: {
    key: 'NCAAB',
    label: 'NCAAB',
    hasPlayers: true,
    hasTeams: true,
    icon: '🏀'
  },
  SOCCER: {
    key: 'SOCCER',
    label: 'Soccer',
    hasPlayers: true,
    hasTeams: true,
    icon: '⚽'
  },
  UFC: {
    key: 'UFC',
    label: 'UFC',
    hasPlayers: true,
    hasTeams: false,
    icon: '🥊'
  },
  TENNIS: {
    key: 'TENNIS',
    label: 'Tennis',
    hasPlayers: true,
    hasTeams: false,
    icon: '🎾'
  }
};

// =========================================================
// TEAM MARKETS (Game-level bets)
// =========================================================

export const TEAM_MARKETS = {
  // Universal team markets (available for all team sports)
  UNIVERSAL: [
    { key: 'h2h', label: 'Moneyline', description: 'Pick the winner', hasLine: false },
    { key: 'spreads', label: 'Spread', description: 'Point spread', hasLine: true },
    { key: 'totals', label: 'Total Points', description: 'Over/Under', hasLine: true }
  ],
  
  // Sport-specific team markets
  NFL: [
    { key: 'team_total', label: 'Team Total', description: 'Team points O/U', hasLine: true },
    { key: 'first_half_spread', label: '1H Spread', description: 'First half spread', hasLine: true },
    { key: 'first_half_total', label: '1H Total', description: 'First half O/U', hasLine: true },
    { key: 'first_quarter_spread', label: '1Q Spread', description: 'First quarter spread', hasLine: true },
    { key: 'first_quarter_total', label: '1Q Total', description: 'First quarter O/U', hasLine: true }
  ],
  
  NBA: [
    { key: 'team_total', label: 'Team Total', description: 'Team points O/U', hasLine: true },
    { key: 'first_half_spread', label: '1H Spread', description: 'First half spread', hasLine: true },
    { key: 'first_half_total', label: '1H Total', description: 'First half O/U', hasLine: true },
    { key: 'first_quarter_spread', label: '1Q Spread', description: 'First quarter spread', hasLine: true },
    { key: 'first_quarter_total', label: '1Q Total', description: 'First quarter O/U', hasLine: true }
  ],
  
  MLB: [
    { key: 'team_total', label: 'Team Total Runs', description: 'Team runs O/U', hasLine: true },
    { key: 'first_5_innings_h2h', label: 'F5 Moneyline', description: 'First 5 innings winner', hasLine: false },
    { key: 'first_5_innings_spread', label: 'F5 Spread', description: 'First 5 innings spread', hasLine: true },
    { key: 'first_5_innings_total', label: 'F5 Total', description: 'First 5 innings O/U', hasLine: true }
  ],
  
  NHL: [
    { key: 'team_total', label: 'Team Total Goals', description: 'Team goals O/U', hasLine: true },
    { key: 'first_period_spread', label: '1P Spread', description: 'First period spread', hasLine: true },
    { key: 'first_period_total', label: '1P Total', description: 'First period O/U', hasLine: true }
  ],
  
  SOCCER: [
    { key: 'team_total', label: 'Team Total Goals', description: 'Team goals O/U', hasLine: true },
    { key: 'draw_no_bet', label: 'Draw No Bet', description: 'Refund if draw', hasLine: false },
    { key: 'double_chance', label: 'Double Chance', description: 'Win or draw', hasLine: false },
    { key: 'both_teams_to_score', label: 'BTTS', description: 'Both teams score', hasLine: false }
  ]
};

// =========================================================
// PLAYER MARKETS BY SPORT & POSITION
// =========================================================

export const PLAYER_MARKETS = {
  NFL: {
    QB: [
      { key: 'player_pass_yds', label: 'Passing Yards', description: 'Total pass yards', hasLine: true },
      { key: 'player_pass_tds', label: 'Passing TDs', description: 'Total pass TDs', hasLine: true },
      { key: 'player_pass_completions', label: 'Completions', description: 'Total completions', hasLine: true },
      { key: 'player_pass_attempts', label: 'Pass Attempts', description: 'Total attempts', hasLine: true },
      { key: 'player_pass_interceptions', label: 'Interceptions', description: 'Total INTs', hasLine: true },
      { key: 'player_pass_longest_completion', label: 'Longest Completion', description: 'Longest pass', hasLine: true },
      { key: 'player_rush_yds', label: 'Rushing Yards', description: 'QB rushing yards', hasLine: true },
      { key: 'player_anytime_td', label: 'Anytime TD', description: 'Score any TD', hasLine: false },
      { key: 'player_first_td', label: 'First TD', description: 'Score first TD', hasLine: false }
    ],
    RB: [
      { key: 'player_rush_yds', label: 'Rushing Yards', description: 'Total rush yards', hasLine: true },
      { key: 'player_rush_attempts', label: 'Rush Attempts', description: 'Total carries', hasLine: true },
      { key: 'player_rush_longest', label: 'Longest Rush', description: 'Longest carry', hasLine: true },
      { key: 'player_reception_yds', label: 'Receiving Yards', description: 'Total rec yards', hasLine: true },
      { key: 'player_receptions', label: 'Receptions', description: 'Total catches', hasLine: true },
      { key: 'player_anytime_td', label: 'Anytime TD', description: 'Score any TD', hasLine: false },
      { key: 'player_first_td', label: 'First TD', description: 'Score first TD', hasLine: false }
    ],
    WR: [
      { key: 'player_reception_yds', label: 'Receiving Yards', description: 'Total rec yards', hasLine: true },
      { key: 'player_receptions', label: 'Receptions', description: 'Total catches', hasLine: true },
      { key: 'player_longest_reception', label: 'Longest Reception', description: 'Longest catch', hasLine: true },
      { key: 'player_anytime_td', label: 'Anytime TD', description: 'Score any TD', hasLine: false },
      { key: 'player_first_td', label: 'First TD', description: 'Score first TD', hasLine: false }
    ],
    TE: [
      { key: 'player_reception_yds', label: 'Receiving Yards', description: 'Total rec yards', hasLine: true },
      { key: 'player_receptions', label: 'Receptions', description: 'Total catches', hasLine: true },
      { key: 'player_longest_reception', label: 'Longest Reception', description: 'Longest catch', hasLine: true },
      { key: 'player_anytime_td', label: 'Anytime TD', description: 'Score any TD', hasLine: false },
      { key: 'player_first_td', label: 'First TD', description: 'Score first TD', hasLine: false }
    ],
    K: [
      { key: 'player_field_goals', label: 'Field Goals Made', description: 'Total FGs made', hasLine: true },
      { key: 'player_kicking_points', label: 'Kicking Points', description: 'Total points', hasLine: true }
    ],
    DEF: [
      { key: 'player_tackles_assists', label: 'Tackles + Assists', description: 'Total tackles', hasLine: true },
      { key: 'player_sacks', label: 'Sacks', description: 'Total sacks', hasLine: true },
      { key: 'player_interceptions', label: 'Interceptions', description: 'Total INTs', hasLine: true }
    ]
  },
  
  NBA: {
    ALL: [ // All positions have same markets in NBA
      { key: 'player_points', label: 'Points', description: 'Total points', hasLine: true },
      { key: 'player_rebounds', label: 'Rebounds', description: 'Total rebounds', hasLine: true },
      { key: 'player_assists', label: 'Assists', description: 'Total assists', hasLine: true },
      { key: 'player_threes', label: '3-Pointers Made', description: 'Total 3PM', hasLine: true },
      { key: 'player_steals', label: 'Steals', description: 'Total steals', hasLine: true },
      { key: 'player_blocks', label: 'Blocks', description: 'Total blocks', hasLine: true },
      { key: 'player_turnovers', label: 'Turnovers', description: 'Total TOs', hasLine: true },
      { key: 'player_pra', label: 'Pts + Rebs + Asts', description: 'Combined PRA', hasLine: true },
      { key: 'player_pr', label: 'Pts + Rebs', description: 'Combined points + rebounds', hasLine: true },
      { key: 'player_pa', label: 'Pts + Asts', description: 'Combined points + assists', hasLine: true },
      { key: 'player_ra', label: 'Rebs + Asts', description: 'Combined rebounds + assists', hasLine: true },
      { key: 'player_double_double', label: 'Double Double', description: '10+ in 2 stats', hasLine: false },
      { key: 'player_triple_double', label: 'Triple Double', description: '10+ in 3 stats', hasLine: false }
    ]
  },
  
  MLB: {
    P: [
      { key: 'player_strikeouts', label: 'Strikeouts', description: 'Total Ks', hasLine: true },
      { key: 'player_hits_allowed', label: 'Hits Allowed', description: 'Total hits', hasLine: true },
      { key: 'player_walks', label: 'Walks', description: 'Total BBs', hasLine: true },
      { key: 'player_earned_runs', label: 'Earned Runs', description: 'Total ERs', hasLine: true },
      { key: 'pitcher_outs', label: 'Pitcher Outs', description: 'Total outs recorded', hasLine: true }
    ],
    BATTER: [
      { key: 'player_hits', label: 'Hits', description: 'Total hits', hasLine: true },
      { key: 'player_total_bases', label: 'Total Bases', description: 'Total bases', hasLine: true },
      { key: 'player_rbis', label: 'RBIs', description: 'Runs batted in', hasLine: true },
      { key: 'player_runs', label: 'Runs Scored', description: 'Total runs', hasLine: true },
      { key: 'player_home_runs', label: 'Home Runs', description: 'Total HRs', hasLine: true },
      { key: 'player_stolen_bases', label: 'Stolen Bases', description: 'Total SBs', hasLine: true },
      { key: 'player_hits_runs_rbis', label: 'H+R+RBI', description: 'Combined', hasLine: true }
    ]
  },
  
  NHL: {
    ALL: [
      { key: 'player_points', label: 'Points', description: 'Goals + assists', hasLine: true },
      { key: 'player_goals', label: 'Goals', description: 'Total goals', hasLine: true },
      { key: 'player_assists', label: 'Assists', description: 'Total assists', hasLine: true },
      { key: 'player_shots_on_goal', label: 'Shots on Goal', description: 'Total SOG', hasLine: true },
      { key: 'player_blocked_shots', label: 'Blocked Shots', description: 'Total blocks', hasLine: true },
      { key: 'player_anytime_goal', label: 'Anytime Goal', description: 'Score any goal', hasLine: false }
    ],
    G: [
      { key: 'goalie_saves', label: 'Saves', description: 'Total saves', hasLine: true },
      { key: 'goalie_goals_allowed', label: 'Goals Allowed', description: 'Total GA', hasLine: true }
    ]
  },
  
  SOCCER: {
    ALL: [
      { key: 'player_goals', label: 'Goals', description: 'Total goals', hasLine: true },
      { key: 'player_assists', label: 'Assists', description: 'Total assists', hasLine: true },
      { key: 'player_shots_on_target', label: 'Shots on Target', description: 'Total SOT', hasLine: true },
      { key: 'player_anytime_goal', label: 'Anytime Goal', description: 'Score any goal', hasLine: false },
      { key: 'player_first_goal', label: 'First Goal', description: 'Score first goal', hasLine: false }
    ],
    GK: [
      { key: 'goalie_saves', label: 'Saves', description: 'Total saves', hasLine: true },
      { key: 'goalie_goals_allowed', label: 'Goals Allowed', description: 'Total GA', hasLine: true }
    ]
  },
  
  TENNIS: {
    ALL: [
      { key: 'player_sets_won', label: 'Sets Won', description: 'Total sets won', hasLine: true },
      { key: 'player_games_won', label: 'Games Won', description: 'Total games won', hasLine: true },
      { key: 'player_aces', label: 'Aces', description: 'Total aces', hasLine: true },
      { key: 'player_double_faults', label: 'Double Faults', description: 'Total DFs', hasLine: true }
    ]
  },
  
  UFC: {
    ALL: [
      { key: 'fighter_method_of_victory', label: 'Method of Victory', description: 'How fighter wins', hasLine: false },
      { key: 'fighter_round_win', label: 'Round of Victory', description: 'Which round', hasLine: false }
    ]
  }
};

// =========================================================
// HELPER FUNCTIONS
// =========================================================

/**
 * Get available markets for a player based on sport and position
 * @param {string} sport - Sport key (e.g., 'NFL', 'NBA')
 * @param {string} position - Player position (e.g., 'QB', 'WR')
 * @returns {Array} Array of available markets
 */
export const getPlayerMarkets = (sport, position) => {
  if (!sport || !PLAYER_MARKETS[sport]) return [];
  
  const sportMarkets = PLAYER_MARKETS[sport];
  
  // NBA, NHL, Soccer, Tennis, UFC - all positions have same markets
  if (sportMarkets.ALL) {
    return sportMarkets.ALL;
  }
  
  // NHL has both ALL and G (goalie) specific
  if (sport === 'NHL') {
    if (position === 'G') {
      return [...sportMarkets.ALL, ...sportMarkets.G];
    }
    return sportMarkets.ALL;
  }
  
  // Soccer has both ALL and GK (goalkeeper) specific
  if (sport === 'SOCCER') {
    if (position === 'GK') {
      return [...sportMarkets.ALL, ...sportMarkets.GK];
    }
    return sportMarkets.ALL;
  }
  
  // NFL, MLB - position-specific markets
  if (!position || !sportMarkets[position]) {
    return [];
  }
  
  return sportMarkets[position];
};

/**
 * Get available team markets for a sport
 * @param {string} sport - Sport key (e.g., 'NFL', 'NBA')
 * @returns {Array} Array of available team markets
 */
export const getTeamMarkets = (sport) => {
  if (!sport) return TEAM_MARKETS.UNIVERSAL;
  
  const sportSpecific = TEAM_MARKETS[sport] || [];
  return [...TEAM_MARKETS.UNIVERSAL, ...sportSpecific];
};

/**
 * Get bet type based on selection
 * @param {boolean} isPlayer - Whether player is selected
 * @param {boolean} isTeam - Whether team is selected
 * @returns {string} Bet type
 */
export const getBetType = (isPlayer, isTeam) => {
  if (isPlayer) return 'player_prop';
  if (isTeam) return 'team_prop';
  return 'other';
};

/**
 * Check if a market requires a line value
 * @param {string} marketKey - Market key
 * @returns {boolean} True if line is required
 */
export const marketRequiresLine = (marketKey) => {
  // Search through all markets to find if this one requires a line
  const allMarkets = [
    ...TEAM_MARKETS.UNIVERSAL,
    ...Object.values(TEAM_MARKETS).flat(),
    ...Object.values(PLAYER_MARKETS).flatMap(sport => 
      Object.values(sport).flat()
    )
  ];
  
  const market = allMarkets.find(m => m.key === marketKey);
  return market?.hasLine ?? true; // Default to requiring line if not found
};

/**
 * Get market label by key
 * @param {string} marketKey - Market key
 * @returns {string} Market label
 */
export const getMarketLabel = (marketKey) => {
  const allMarkets = [
    ...TEAM_MARKETS.UNIVERSAL,
    ...Object.values(TEAM_MARKETS).flat(),
    ...Object.values(PLAYER_MARKETS).flatMap(sport => 
      Object.values(sport).flat()
    )
  ];
  
  const market = allMarkets.find(m => m.key === marketKey);
  return market?.label || marketKey;
};

// =========================================================
// POSITION MAPPINGS
// =========================================================

export const POSITIONS_BY_SPORT = {
  NFL: ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'],
  NBA: ['PG', 'SG', 'SF', 'PF', 'C'],
  MLB: ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH'],
  NHL: ['C', 'LW', 'RW', 'D', 'G'],
  SOCCER: ['GK', 'DEF', 'MID', 'FWD'],
  NCAAF: ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'],
  NCAAB: ['G', 'F', 'C']
};

export default {
  SPORTS,
  TEAM_MARKETS,
  PLAYER_MARKETS,
  POSITIONS_BY_SPORT,
  getPlayerMarkets,
  getTeamMarkets,
  getBetType,
  marketRequiresLine,
  getMarketLabel
};
