-- KBO 야구 승부예측 AI — 초기 DB 스키마
-- Docker 컨테이너 최초 실행 시 자동 적용됩니다.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. teams
CREATE TABLE IF NOT EXISTS teams (
  id           SERIAL PRIMARY KEY,
  short_name   VARCHAR(20)  NOT NULL UNIQUE,
  full_name    VARCHAR(50)  NOT NULL,
  stadium      VARCHAR(100),
  is_dome      BOOLEAN      NOT NULL DEFAULT FALSE
);

-- 2. players
CREATE TABLE IF NOT EXISTS players (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(50)  NOT NULL,
  team_id     INT          NOT NULL REFERENCES teams(id),
  position    VARCHAR(20),
  throw_hand  VARCHAR(10),
  is_foreign  BOOLEAN      NOT NULL DEFAULT FALSE,
  is_active   BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

-- 3. games
CREATE TABLE IF NOT EXISTS games (
  id              SERIAL PRIMARY KEY,
  season          SMALLINT    NOT NULL,
  scheduled_at    TIMESTAMPTZ NOT NULL,
  home_team_id    INT         NOT NULL REFERENCES teams(id),
  away_team_id    INT         NOT NULL REFERENCES teams(id),
  home_score      SMALLINT,
  away_score      SMALLINT,
  status          VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
  stadium         VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_games_scheduled_at ON games(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);

-- 4. game_predictions
CREATE TABLE IF NOT EXISTS game_predictions (
  id                  SERIAL PRIMARY KEY,
  game_id             INT          NOT NULL REFERENCES games(id),
  home_starter_id     INT          REFERENCES players(id),
  away_starter_id     INT          REFERENCES players(id),
  home_win_prob       NUMERIC(5,4),
  away_win_prob       NUMERIC(5,4),
  confidence_level    VARCHAR(10),
  xgboost_home_prob   NUMERIC(5,4),
  lstm_home_prob      NUMERIC(5,4),
  model_version       VARCHAR(50),
  features_used       INT,
  prediction_reason   VARCHAR(2000),
  is_final            BOOLEAN      NOT NULL DEFAULT FALSE,
  predicted_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_game_id ON game_predictions(game_id);

-- 5. pitcher_game_stats
CREATE TABLE IF NOT EXISTS pitcher_game_stats (
  id               SERIAL PRIMARY KEY,
  player_id        INT         NOT NULL REFERENCES players(id),
  game_id          INT         NOT NULL REFERENCES games(id),
  is_starter       BOOLEAN     NOT NULL DEFAULT FALSE,
  innings_pitched  NUMERIC(5,1),
  earned_runs      SMALLINT,
  strikeouts       SMALLINT,
  walks            SMALLINT,
  hits_allowed     SMALLINT,
  era              NUMERIC(5,2),
  whip             NUMERIC(5,2),
  UNIQUE(player_id, game_id)
);

-- 6. team_game_stats
CREATE TABLE IF NOT EXISTS team_game_stats (
  id            SERIAL PRIMARY KEY,
  team_id       INT      NOT NULL REFERENCES teams(id),
  game_id       INT      NOT NULL REFERENCES games(id),
  runs_scored   SMALLINT,
  runs_allowed  SMALLINT,
  hits          SMALLINT,
  errors        SMALLINT,
  UNIQUE(team_id, game_id)
);

-- 7. team_daily_snapshots
CREATE TABLE IF NOT EXISTS team_daily_snapshots (
  id              SERIAL PRIMARY KEY,
  team_id         INT  NOT NULL REFERENCES teams(id),
  snapshot_date   DATE NOT NULL,
  rank            SMALLINT,
  games_played    SMALLINT,
  wins            SMALLINT,
  losses          SMALLINT,
  draws           SMALLINT,
  season_win_rate NUMERIC(4,3),
  last10_wins     SMALLINT,
  last10_losses   SMALLINT,
  streak_type     VARCHAR(10),
  streak_count    SMALLINT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(team_id, snapshot_date)
);

-- 8. crawl_logs
CREATE TABLE IF NOT EXISTS crawl_logs (
  id                SERIAL PRIMARY KEY,
  source            VARCHAR(50) NOT NULL,
  task_type         VARCHAR(50) NOT NULL,
  status            VARCHAR(20) NOT NULL,
  records_collected INT         NOT NULL DEFAULT 0,
  error_message     TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. player_season_stats
CREATE TABLE IF NOT EXISTS player_season_stats (
  id              SERIAL PRIMARY KEY,
  player_id       INT      NOT NULL REFERENCES players(id),
  season          SMALLINT NOT NULL,
  avg             NUMERIC(4,3),
  obp             NUMERIC(4,3),
  slg             NUMERIC(4,3),
  ops             NUMERIC(5,3),
  hr              SMALLINT,
  rbi             SMALLINT,
  sb              SMALLINT,
  war_batter      NUMERIC(4,2),
  era             NUMERIC(5,2),
  whip            NUMERIC(5,2),
  fip             NUMERIC(5,2),
  innings_pitched NUMERIC(5,1),
  strikeouts      SMALLINT,
  walks           SMALLINT,
  war_pitcher     NUMERIC(4,2),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(player_id, season)
);

-- 10. team_season_stats
CREATE TABLE IF NOT EXISTS team_season_stats (
  id              SERIAL PRIMARY KEY,
  team_id         INT      NOT NULL REFERENCES teams(id),
  season          SMALLINT NOT NULL,
  wins            SMALLINT,
  losses          SMALLINT,
  draws           SMALLINT,
  win_rate        NUMERIC(4,3),
  runs_scored     INT,
  runs_allowed    INT,
  team_era        NUMERIC(5,2),
  team_ops        NUMERIC(5,3),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(team_id, season)
);

-- ============================================================
-- 초기 데이터 — KBO 10개 구단
-- ============================================================
INSERT INTO teams (short_name, full_name, stadium, is_dome) VALUES
  ('두산',   '두산 베어스',    '잠실야구장',            FALSE),
  ('LG',     'LG 트윈스',      '잠실야구장',            FALSE),
  ('키움',   '키움 히어로즈',  '고척스카이돔',          TRUE),
  ('KT',     'KT 위즈',        '수원KT위즈파크',        FALSE),
  ('SSG',    'SSG 랜더스',     '인천SSG랜더스필드',     FALSE),
  ('NC',     'NC 다이노스',    '창원NC파크',            FALSE),
  ('KIA',    'KIA 타이거즈',   '광주-기아챔피언스필드', FALSE),
  ('롯데',   '롯데 자이언츠',  '사직야구장',            FALSE),
  ('삼성',   '삼성 라이온즈',  '대구삼성라이온즈파크',  FALSE),
  ('한화',   '한화 이글스',    '한화생명이글스파크',    FALSE)
ON CONFLICT DO NOTHING;
