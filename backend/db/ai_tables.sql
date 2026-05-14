-- ============================================================
-- AI & 크롤링 파트 추가 테이블 마이그레이션
-- backend/db/init.sql 이후에 실행하세요.
--
-- 적용 방법:
--   docker exec -i kbo_postgres psql -U kbo_user -d kbo_predict < db/ai_tables.sql
-- ============================================================

-- team_daily_snapshots: 일별 팀 순위 스냅샷
-- "2024년 5월 1일 경기"를 예측할 때 그 시점에 알 수 있는 팀 정보만 사용 (look-ahead bias 방지)
CREATE TABLE IF NOT EXISTS team_daily_snapshots (
  id              SERIAL PRIMARY KEY,
  team_id         INT NOT NULL REFERENCES teams(id),
  snapshot_date   DATE NOT NULL,
  rank            SMALLINT,
  games_played    SMALLINT,
  wins            SMALLINT,
  losses          SMALLINT,
  draws           SMALLINT,
  season_win_rate DECIMAL(4,3),
  last10_wins     SMALLINT,
  last10_losses   SMALLINT,
  streak_type     VARCHAR(10),     -- 'WIN' | 'LOSS' | 'DRAW'
  streak_count    SMALLINT,
  created_at      TIMESTAMP DEFAULT NOW(),
  UNIQUE(team_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_team_snapshots_date ON team_daily_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_team_snapshots_team_date ON team_daily_snapshots(team_id, snapshot_date);

-- player_season_stats: 선수 시즌 누적 통계
CREATE TABLE IF NOT EXISTS player_season_stats (
  id              SERIAL PRIMARY KEY,
  player_id       INT NOT NULL REFERENCES players(id),
  season          SMALLINT NOT NULL,
  -- 타자 스탯
  avg             DECIMAL(4,3),
  obp             DECIMAL(4,3),
  slg             DECIMAL(4,3),
  ops             DECIMAL(5,3),
  hr              SMALLINT,
  rbi             SMALLINT,
  sb              SMALLINT,
  war_batter      DECIMAL(4,2),
  -- 투수 스탯
  era             DECIMAL(5,2),
  whip            DECIMAL(5,2),
  fip             DECIMAL(5,2),
  innings_pitched DECIMAL(5,1),
  strikeouts      SMALLINT,
  walks           SMALLINT,
  war_pitcher     DECIMAL(4,2),
  updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(player_id, season)
);

-- team_season_stats: 팀 시즌 합산 통계
CREATE TABLE IF NOT EXISTS team_season_stats (
  id            SERIAL PRIMARY KEY,
  team_id       INT NOT NULL REFERENCES teams(id),
  season        SMALLINT NOT NULL,
  team_ops      DECIMAL(5,3),
  team_era      DECIMAL(5,2),
  runs_scored   INT,
  runs_allowed  INT,
  win_rate      DECIMAL(4,3),
  updated_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(team_id, season)
);

-- game_predictions: ML 예측 결과
CREATE TABLE IF NOT EXISTS game_predictions (
  id                 SERIAL PRIMARY KEY,
  game_id            INT NOT NULL REFERENCES games(id),
  home_starter_id    INT REFERENCES players(id),
  away_starter_id    INT REFERENCES players(id),
  home_win_prob      DECIMAL(5,4),
  away_win_prob      DECIMAL(5,4),
  confidence_level   VARCHAR(10),    -- 'HIGH' | 'MEDIUM' | 'LOW'
  xgboost_home_prob  DECIMAL(5,4),
  lstm_home_prob     DECIMAL(5,4),
  model_version      VARCHAR(50),
  features_used      INT,
  prediction_reason  TEXT,
  is_final           BOOLEAN DEFAULT FALSE,
  predicted_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_predictions_game_id ON game_predictions(game_id);
CREATE INDEX IF NOT EXISTS idx_game_predictions_predicted_at ON game_predictions(predicted_at);

-- pitcher_game_stats: 투수 경기별 기록
CREATE TABLE IF NOT EXISTS pitcher_game_stats (
  id              SERIAL PRIMARY KEY,
  player_id       INT NOT NULL REFERENCES players(id),
  game_id         INT NOT NULL REFERENCES games(id),
  is_starter      BOOLEAN DEFAULT FALSE,
  innings_pitched DECIMAL(5,1),
  earned_runs     SMALLINT,
  strikeouts      SMALLINT,
  walks           SMALLINT,
  hits_allowed    SMALLINT,
  era             DECIMAL(5,2),
  whip            DECIMAL(5,2)
);

CREATE INDEX IF NOT EXISTS idx_pitcher_game_stats_player ON pitcher_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pitcher_game_stats_game ON pitcher_game_stats(game_id);

-- team_game_stats: 팀 경기별 기록
CREATE TABLE IF NOT EXISTS team_game_stats (
  id            SERIAL PRIMARY KEY,
  team_id       INT NOT NULL REFERENCES teams(id),
  game_id       INT NOT NULL REFERENCES games(id),
  runs_scored   SMALLINT,
  runs_allowed  SMALLINT,
  hits          SMALLINT,
  errors        SMALLINT
);

CREATE INDEX IF NOT EXISTS idx_team_game_stats_team ON team_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_team_game_stats_game ON team_game_stats(game_id);

-- crawl_logs: 크롤링 이력 로그
CREATE TABLE IF NOT EXISTS crawl_logs (
  id                SERIAL PRIMARY KEY,
  source            VARCHAR(50) NOT NULL,    -- 'kbo_official' | 'statiz' | 'naver' | 'weather'
  task_type         VARCHAR(50) NOT NULL,    -- 'team_rank' | 'pitcher_season_stats' | ...
  status            VARCHAR(20) NOT NULL,    -- 'SUCCESS' | 'FAILED'
  records_collected INT DEFAULT 0,
  error_message     TEXT,
  created_at        TIMESTAMP DEFAULT NOW()
);

-- 확인 쿼리
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'team_daily_snapshots', 'player_season_stats', 'team_season_stats',
    'game_predictions', 'pitcher_game_stats', 'team_game_stats', 'crawl_logs'
  )
ORDER BY table_name;
