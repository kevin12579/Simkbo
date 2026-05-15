export interface Team {
  id: number;
  name: string;
  short_name: string;
  logo_url?: string;
  home_stadium?: string;
}

export interface StarterInfo {
  player_id: number;
  name: string;
  recent_era?: number;
}

export interface Prediction {
  home_win_prob: number;
  away_win_prob: number;
  confidence_level: "HIGH" | "MEDIUM" | "LOW";
  home_starter?: StarterInfo;
  away_starter?: StarterInfo;
  updated_at: string;
  ai_reasoning?: string;
  xgboost_home_prob?: number;
  lstm_home_prob?: number;
  model_version?: string;
}

export interface GameCard {
  game_id: number;
  scheduled_at: string;
  stadium?: string;
  status: "SCHEDULED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED" | "POSTPONED";
  home_team: Team;
  away_team: Team;
  prediction?: Prediction;
}

export interface TodayGamesResponse {
  date: string;
  games: GameCard[];
  total: number;
}

export interface TeamStats {
  team: Team;
  recent_stats: {
    last_n_games: number;
    wins: number;
    losses: number;
    win_rate: number;
    avg_runs_scored: number;
    home_record: { wins: number; losses: number };
    away_record: { wins: number; losses: number };
    streak: string;
  };
  updated_at: string;
}

export interface PitcherGameRecord {
  game_id: number;
  innings_pitched?: number;
  earned_runs?: number;
  strikeouts?: number;
  walks?: number;
  hits_allowed?: number;
  era?: number;
  whip?: number;
}

export interface PitcherStats {
  player_id: number;
  name: string;
  team_name: string;
  recent_games: PitcherGameRecord[];
}
