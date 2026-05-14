# ⚾ KBO 야구 승부예측 AI 서비스 — MVP 설계 문서

> **프로젝트**: KBO 야구 승부예측 AI 서비스  
> **버전**: v1.0 (MVP P0)  
> **개발 기간**: 2주 스프린트  
> **범위**: P0 필수 기능 (오늘의 경기 예측 / 예측 상세 보기 / 팀·선수 통계 보기)

---

## 목차

1. [IA (정보구조도)](#1-ia-정보구조도)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [데이터베이스 설계](#3-데이터베이스-설계)
4. [API 명세](#4-api-명세)
5. [파일 구조도](#5-파일-구조도)

---

## 1. IA (정보구조도)

### 1-1. 트리(Tree) 구조 IA — P0 범위

```
KBO 야구 승부예측 AI
│
├── 홈 (Home)                          [HOME001]
│   └── 오늘의 경기 예측 카드 목록        [HOME002]
│       ├── 경기 카드 (홈팀 vs 원정팀)
│       ├── 승리 확률 바
│       ├── 신뢰도 별점
│       └── 선발 투수 요약
│
├── 경기 상세 (Game Detail)             [GAME001]
│   ├── 승리 확률 상세                   [GAME002]
│   │   ├── 홈팀 / 원정팀 확률 바
│   │   └── XGBoost + DL 앙상블 결과
│   └── AI 예측 근거                    [GAME003]
│       ├── 선발 투수 분석
│       ├── 팀 최근 폼 분석
│       └── 핵심 변수 요약 (3~5줄)
│
└── 통계 (Statistics)                   [STAT001]
    ├── 팀 통계                          [STAT002]
    │   ├── 최근 10경기 승률
    │   ├── OPS / 평균 득점
    │   └── 홈/원정 구분 성적
    └── 선발 투수 정보                   [STAT003]
        ├── 최근 5경기 ERA / WHIP
        ├── 탈삼진
        └── 상대 타선 대비 성적
```

### 1-2. 스프레드시트 형식 IA

| Depth | Code | 화면명 | 페이지 정의 / 요구사항 | 개발 구분 | 논의 사항 |
|-------|------|--------|----------------------|-----------|-----------|
| 1 | HOME001 | 홈 | 서비스 진입 화면. 당일 KBO 전경기 예측 카드 목록 노출. 경기가 없는 날은 "오늘 경기 없음" 안내 | P0 | 경기 없는 날 UI 처리 필요 |
| 2 | HOME002 | 오늘의 경기 목록 | 홈팀/원정팀 로고·이름, 승리 확률 바, 신뢰도 별점, 선발 투수명/ERA, 예측 업데이트 시각 표시. 카드 클릭 시 GAME001로 이동 | P0 | 선발 미확정 시 "TBD" 표시 + 신뢰도 낮게 처리 |
| 1 | GAME001 | 경기 상세 | 특정 경기의 예측 상세 페이지. URL: /games/[id] | P0 | - |
| 2 | GAME002 | 승리 확률 상세 | 홈팀/원정팀 승리 확률 수치 + 시각화 바. XGBoost 단독 / DL 앙상블 결과 병렬 표시 | P0 | 두 모델 결과 차이 클 때 UX 처리 |
| 2 | GAME003 | AI 예측 근거 | Claude API 생성 자연어 근거 텍스트 (3~5줄). 선발 투수 분석·팀 폼·핵심 변수 포함 | P0 | AI 생성 실패 시 Fallback 문구 처리 |
| 1 | STAT001 | 통계 | 팀별·선수별 통계 허브 페이지. URL: /stats | P0 | - |
| 2 | STAT002 | 팀 통계 | 10개 KBO 팀 최근 폼 테이블. 최근 10경기 승률, OPS, 평균 득점. 홈/원정 구분 탭 | P0 | 시즌 전환 시 데이터 리셋 처리 |
| 2 | STAT003 | 선발 투수 정보 | 당일 선발 예정 투수 카드. 최근 5경기 ERA·WHIP·탈삼진, 상대 타선 대비 성적 | P0 | 선발 미확정 투수 처리 |

### 1-3. 화면 코드 규칙

```
{영역코드}{3자리 순번}
HOME = 홈/메인
GAME = 경기 관련
STAT = 통계 관련

예: GAME001 = 경기 영역 첫 번째 화면
```

### 1-4. IA → 다음 산출물 연결

```
요구사항 정의 (기획서 v1.0)
    ↓
IA (정보구조도) ← 현재 단계
    ↓
와이어프레임 (FigJam / Excalidraw 권장)
    ↓
컴포넌트 설계 (스토리보드)
    ↓
디자인 & 개발
```

---

## 2. 시스템 아키텍처

### 2-1. 전체 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                            │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Next.js 14 (App Router)                     │  │
│   │   HOME001 카드 목록 / GAME001 상세 / STAT001 통계         │  │
│   └──────────────────────────────────────────────────────────┘  │
│                           ↕ HTTPS / REST API                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LAYER                                │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                  FastAPI (API Server)                    │  │
│   │   /api/v1/games  /api/v1/teams  /api/v1/predictions     │  │
│   └───────────────┬──────────────────────┬───────────────────┘  │
│                   │                      │                      │
│   ┌───────────────▼───────┐   ┌──────────▼──────────────────┐  │
│   │  ML/AI Prediction     │   │  APScheduler (자동화)        │  │
│   │  ┌─────────────────┐  │   │  ┌──────────────────────┐   │  │
│   │  │ XGBoost Model   │  │   │  │ 매일 09:00           │   │  │
│   │  │ (Stage 1)       │  │   │  │ 전날 경기 결과 수집   │   │  │
│   │  └─────────────────┘  │   │  ├──────────────────────┤   │  │
│   │  ┌─────────────────┐  │   │  │ 매일 18:00           │   │  │
│   │  │ PyTorch Model   │  │   │  │ 선발 투수 + 날씨     │   │  │
│   │  │ (Stage 2)       │  │   │  ├──────────────────────┤   │  │
│   │  └─────────────────┘  │   │  │ 매일 20:00           │   │  │
│   │  ┌─────────────────┐  │   │  │ 최종 예측 업데이트   │   │  │
│   │  │ Claude API      │  │   │  └──────────────────────┘   │  │
│   │  │ 근거 생성       │  │   └─────────────────────────────┘  │
│   │  └─────────────────┘  │                                    │
│   └───────────────────────┘                                    │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Python Crawler (데이터 수집)                │  │
│   │   statiz.co.kr · 네이버스포츠 · 기상청 API · Odds API   │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                                │
│                                                                 │
│   ┌──────────────────────┐    ┌───────────────────────────┐    │
│   │    PostgreSQL         │    │    Redis                  │    │
│   │  (정형 데이터 영속화) │    │  (예측 결과 캐싱)         │    │
│   │  teams / games        │    │  TTL: 30분 (예측 캐시)   │    │
│   │  players / stats      │    │  TTL: 1시간 (팀 통계)    │    │
│   │  predictions          │    └───────────────────────────┘    │
│   └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   DEPLOY (Railway / AWS EC2)                    │
│   Backend: Dockerfile + uvicorn   Frontend: Vercel / Railway    │
└─────────────────────────────────────────────────────────────────┘
```

### 2-2. 아키텍처 패턴

**레이어드 아키텍처(Layered)** 채택 — 3-Tier (Presentation / Business / Data)

MVP 단계이므로 **모놀리식**에 가까운 단순 구조를 유지하고, MAU 증가 시 서비스 분리 (ML 서버 분리 → Celery Worker 도입)를 점진적으로 적용한다.

### 2-3. 데이터 흐름

```
[외부 데이터 소스]
statiz.co.kr / 네이버스포츠 / 기상청 / Odds API
        │
        ▼ (APScheduler 자동 실행)
[Python Crawler]
        │
        ▼ (저장)
[PostgreSQL] ──────────────────────▶ [XGBoost + PyTorch]
                                              │
                                              ▼ (예측값)
                                    [Claude API 근거 생성]
                                              │
                                              ▼ (저장)
                                    [PostgreSQL: game_predictions]
                                              │
                                              ▼ (캐싱)
                                         [Redis]
                                              │
                                              ▼ (API 응답)
                                     [FastAPI] ──▶ [Next.js]
```

### 2-4. 확장성 설계 (MVP → Production)

| 단계 | 구조 | 비고 |
|------|------|------|
| MVP (현재) | 단일 FastAPI 서버 + PostgreSQL + Redis | Railway 단일 서비스 |
| 1차 확장 | ML 예측 → Celery Worker 분리 | 예측 처리 시간이 API 응답을 막지 않도록 |
| 2차 확장 | 읽기 DB 복제(Read Replica) | 트래픽 증가 시 조회 부하 분산 |
| 3차 확장 | CDN(Cloudflare) + 수평 확장 | MAU 1만 이후 |

### 2-5. 아키텍처 핵심 체크리스트

- [x] 단일 장애점(SPOF): Railway 자동 재시작 + Redis 장애 시 DB 직접 조회 Fallback
- [x] 스케줄러 중복 실행 방지: APScheduler `max_instances=1` 설정
- [x] 크롤링 차단 대응: 요청 간격 1~2초, User-Agent 로테이션
- [x] 선발 미확정 대응: 신뢰도 `LOW`로 표시, 팀 통계 기반 예측만 노출
- [x] AI API 실패 대응: Claude API 실패 시 사전 정의된 템플릿 근거 사용

---

## 3. 데이터베이스 설계

> 기술 스택: **PostgreSQL** + **Redis**  
> 설계 원칙: 비식별 관계(인조 PK), 비정규화 금지(사건형 테이블 제외), 3NF 준수

### 3-1. ERD 개요

```
teams ──< players (1:N)
teams ──< games (홈팀, 1:N)
teams ──< games (원정팀, 1:N)
games ──< game_predictions (1:N)
games ──< pitcher_game_stats (1:N)
games ──< team_game_stats (1:N)
players ──< pitcher_game_stats (1:N)
teams ──< team_game_stats (1:N)
game_predictions >── players (선발 투수, N:1)
games ──< crawl_logs (참조용, 관계 없음)
```

### 3-2. 테이블 설계 원칙

- 모든 테이블 인조 PK (`SERIAL` / `BIGSERIAL`) 사용
- 날짜: `TIMESTAMP` (DATETIME 동등, 2038년 문제 없음, 타임존 KST 수동 처리)
- 문자열: `VARCHAR` (조회 비율 8:2)
- N:M 관계는 중간 테이블로 분해
- 사건형 테이블(`game_predictions`, `pitcher_game_stats`)은 계산값 저장 허용 (이력 보존)

### 3-3. PostgreSQL DDL (SQL)

```sql
-- ============================================================
-- 0. 확장 및 초기 설정
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. teams (팀 정보)
-- ============================================================
CREATE TABLE teams (
  id            SERIAL PRIMARY KEY,
  name          VARCHAR(50)  NOT NULL UNIQUE,        -- 예: 두산 베어스
  short_name    VARCHAR(20)  NOT NULL UNIQUE,        -- 예: 두산
  logo_url      VARCHAR(255),
  home_stadium  VARCHAR(100),
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  teams IS 'KBO 10개 구단 정보';
COMMENT ON COLUMN teams.short_name IS '카드 UI 표시용 약칭';

-- ============================================================
-- 2. players (선수 정보 — MVP는 투수 중심)
-- ============================================================
CREATE TABLE players (
  id          SERIAL PRIMARY KEY,
  team_id     INT          NOT NULL REFERENCES teams(id),
  name        VARCHAR(50)  NOT NULL,
  position    VARCHAR(20)  NOT NULL,                 -- 'PITCHER' | 'BATTER'
  throw_hand  VARCHAR(10),                           -- 'LEFT' | 'RIGHT'
  bat_hand    VARCHAR(10),                           -- 'LEFT' | 'RIGHT' | 'SWITCH'
  is_foreign  BOOLEAN      NOT NULL DEFAULT FALSE,
  is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_players_position ON players(position);

-- ============================================================
-- 3. games (경기 일정 및 결과)
-- ============================================================
CREATE TABLE games (
  id              SERIAL PRIMARY KEY,
  home_team_id    INT         NOT NULL REFERENCES teams(id),
  away_team_id    INT         NOT NULL REFERENCES teams(id),
  scheduled_at    TIMESTAMP   NOT NULL,              -- KST 경기 시작 시각
  stadium         VARCHAR(100),
  home_score      SMALLINT,                          -- 경기 종료 후 기록
  away_score      SMALLINT,
  status          VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
                  -- 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'POSTPONED'
  season          SMALLINT    NOT NULL,              -- 연도: 2024, 2025 ...
  created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_different_teams CHECK (home_team_id <> away_team_id)
);

CREATE INDEX idx_games_scheduled_at ON games(scheduled_at);
CREATE INDEX idx_games_home_team_id ON games(home_team_id);
CREATE INDEX idx_games_away_team_id ON games(away_team_id);
CREATE INDEX idx_games_status ON games(status);
-- 오늘의 경기 조회용 복합 인덱스
CREATE INDEX idx_games_date_status ON games(DATE(scheduled_at), status);

-- ============================================================
-- 4. game_predictions (예측 결과 — 사건형 테이블)
-- ============================================================
-- 사건형: 한번 기록되면 수정·삭제 드뭄. 계산값 저장 허용.
-- 선발 확정 전/후 여러 버전 기록 (is_final로 최신 확정본 구분)
CREATE TABLE game_predictions (
  id                        SERIAL     PRIMARY KEY,
  game_id                   INT        NOT NULL REFERENCES games(id),
  home_win_prob             DECIMAL(5,4) NOT NULL,   -- 0.0000 ~ 1.0000
  away_win_prob             DECIMAL(5,4) NOT NULL,   -- home + away = 1.0000
  confidence_level          VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
                            -- 'HIGH' | 'MEDIUM' | 'LOW' (선발 미확정 시 LOW)
  xgboost_home_prob         DECIMAL(5,4),
  pytorch_home_prob         DECIMAL(5,4),
  ensemble_weight_xgb       DECIMAL(3,2) DEFAULT 0.60, -- XGBoost 앙상블 가중치
  ai_reasoning              TEXT,                    -- Claude API 생성 근거
  home_starter_id           INT REFERENCES players(id),
  away_starter_id           INT REFERENCES players(id),
  is_final                  BOOLEAN    NOT NULL DEFAULT FALSE, -- 최종 예측본
  model_version             VARCHAR(20),             -- 예: 'v1.0-xgb+lstm'
  predicted_at              TIMESTAMP  NOT NULL DEFAULT NOW(),
  actual_result             VARCHAR(10),             -- 'HOME_WIN' | 'AWAY_WIN' | NULL
  CONSTRAINT chk_prob_sum CHECK (
    ABS((home_win_prob + away_win_prob) - 1.0) < 0.0001
  )
);

CREATE INDEX idx_predictions_game_id ON game_predictions(game_id);
CREATE INDEX idx_predictions_is_final ON game_predictions(game_id, is_final);
CREATE INDEX idx_predictions_predicted_at ON game_predictions(predicted_at);

-- ============================================================
-- 5. pitcher_game_stats (선발 투수 경기별 기록 — 사건형)
-- ============================================================
CREATE TABLE pitcher_game_stats (
  id               SERIAL     PRIMARY KEY,
  player_id        INT        NOT NULL REFERENCES players(id),
  game_id          INT        NOT NULL REFERENCES games(id),
  is_starter       BOOLEAN    NOT NULL DEFAULT TRUE,
  innings_pitched  DECIMAL(4,1),
  hits_allowed     SMALLINT,
  earned_runs      SMALLINT,
  walks            SMALLINT,
  strikeouts       SMALLINT,
  era              DECIMAL(5,2),                     -- 저장: 이력 보존 목적
  whip             DECIMAL(5,2),                     -- 저장: 이력 보존 목적
  created_at       TIMESTAMP  NOT NULL DEFAULT NOW(),
  UNIQUE(player_id, game_id)
);

CREATE INDEX idx_pitcher_stats_player_id ON pitcher_game_stats(player_id);
CREATE INDEX idx_pitcher_stats_game_id ON pitcher_game_stats(game_id);

-- ============================================================
-- 6. team_game_stats (팀 경기별 타선 기록 — 사건형)
-- ============================================================
CREATE TABLE team_game_stats (
  id            SERIAL     PRIMARY KEY,
  team_id       INT        NOT NULL REFERENCES teams(id),
  game_id       INT        NOT NULL REFERENCES games(id),
  is_home       BOOLEAN    NOT NULL,
  runs_scored   SMALLINT,
  hits          SMALLINT,
  home_runs     SMALLINT,
  ops           DECIMAL(5,3),                        -- 저장: 이력 보존 목적
  batting_avg   DECIMAL(4,3),
  created_at    TIMESTAMP  NOT NULL DEFAULT NOW(),
  UNIQUE(team_id, game_id)
);

CREATE INDEX idx_team_stats_team_id ON team_game_stats(team_id);
CREATE INDEX idx_team_stats_game_id ON team_game_stats(game_id);

-- ============================================================
-- 7. crawl_logs (데이터 수집 이력)
-- ============================================================
CREATE TABLE crawl_logs (
  id                SERIAL     PRIMARY KEY,
  source            VARCHAR(50) NOT NULL,            -- 'statiz' | 'naver' | 'weather' | 'odds'
  task_type         VARCHAR(50) NOT NULL,            -- 'game_result' | 'pitcher_info' | 'schedule'
  status            VARCHAR(20) NOT NULL,            -- 'SUCCESS' | 'FAILED' | 'PARTIAL'
  records_collected INT         NOT NULL DEFAULT 0,
  error_message     TEXT,
  crawled_at        TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crawl_logs_crawled_at ON crawl_logs(crawled_at);
CREATE INDEX idx_crawl_logs_source ON crawl_logs(source, status);

-- ============================================================
-- 8. 초기 데이터 — KBO 10개 구단
-- ============================================================
INSERT INTO teams (name, short_name, home_stadium) VALUES
  ('두산 베어스',   '두산',   '잠실야구장'),
  ('LG 트윈스',    'LG',     '잠실야구장'),
  ('키움 히어로즈', '키움',   '고척스카이돔'),
  ('KT 위즈',      'KT',     '수원KT위즈파크'),
  ('SSG 랜더스',   'SSG',    '인천SSG랜더스필드'),
  ('NC 다이노스',   'NC',    '창원NC파크'),
  ('KIA 타이거즈', 'KIA',    '광주-기아챔피언스필드'),
  ('롯데 자이언츠', '롯데',   '사직야구장'),
  ('삼성 라이온즈', '삼성',   '대구삼성라이온즈파크'),
  ('한화 이글스',  '한화',    '한화생명이글스파크');
```

### 3-4. Redis 캐싱 전략

| 키 패턴 | 저장 데이터 | TTL | Invalidation |
|---------|------------|-----|--------------|
| `predictions:today` | 오늘의 경기 예측 전체 리스트 | 30분 | 예측 업데이트 시 삭제 |
| `prediction:{game_id}` | 개별 경기 예측 상세 | 30분 | 예측 업데이트 시 삭제 |
| `team_stats:{team_id}` | 팀 최근 통계 | 1시간 | 크롤 완료 시 삭제 |
| `pitcher_stats:{player_id}` | 투수 최근 5경기 통계 | 1시간 | 크롤 완료 시 삭제 |

---

## 4. API 명세

> **Base URL**: `https://api.kbo-predict.com/api/v1`  
> **인증**: MVP 단계 — 없음 (Public API)  
> **응답 형식**: JSON  
> **HTTP 메서드**: GET 위주 (예측 트리거만 POST)

---

### 4-1. 오늘의 경기 예측 목록

```
GET /games/today
```

**설명**: 당일 KBO 전 경기의 예측 카드 데이터 반환. Redis 캐싱 우선 조회.

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| date | string | N | 오늘(KST) | 조회 날짜 (YYYY-MM-DD) |

**Response 200**

```json
{
  "date": "2025-05-10",
  "games": [
    {
      "game_id": 1,
      "scheduled_at": "2025-05-10T18:30:00+09:00",
      "stadium": "잠실야구장",
      "status": "SCHEDULED",
      "home_team": {
        "id": 1,
        "name": "두산 베어스",
        "short_name": "두산",
        "logo_url": "https://..."
      },
      "away_team": {
        "id": 2,
        "name": "LG 트윈스",
        "short_name": "LG",
        "logo_url": "https://..."
      },
      "prediction": {
        "home_win_prob": 0.6200,
        "away_win_prob": 0.3800,
        "confidence_level": "HIGH",
        "home_starter": {
          "player_id": 10,
          "name": "곽빈",
          "recent_era": 1.80
        },
        "away_starter": {
          "player_id": 25,
          "name": "임찬규",
          "recent_era": 3.45
        },
        "updated_at": "2025-05-10T20:00:00+09:00"
      }
    }
  ],
  "total": 5
}
```

**Response 예외**

| 상태 코드 | 설명 |
|----------|------|
| 200 | 성공 (경기 없는 날: `"games": [], "total": 0`) |
| 500 | 서버 내부 오류 |

---

### 4-2. 경기 상세 예측

```
GET /games/{game_id}/prediction
```

**설명**: 특정 경기의 상세 예측 결과 + AI 생성 근거 반환.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| game_id | integer | Y | 경기 ID |

**Response 200**

```json
{
  "game_id": 1,
  "scheduled_at": "2025-05-10T18:30:00+09:00",
  "stadium": "잠실야구장",
  "status": "SCHEDULED",
  "home_team": {
    "id": 1,
    "name": "두산 베어스",
    "logo_url": "https://..."
  },
  "away_team": {
    "id": 2,
    "name": "LG 트윈스",
    "logo_url": "https://..."
  },
  "prediction": {
    "home_win_prob": 0.6200,
    "away_win_prob": 0.3800,
    "confidence_level": "HIGH",
    "xgboost_home_prob": 0.6050,
    "pytorch_home_prob": 0.6480,
    "model_version": "v1.0-xgb+lstm",
    "ai_reasoning": "두산 선발 곽빈은 최근 3경기 평균 ERA 1.80으로 최상의 컨디션입니다. 잠실 홈 구장에서 최근 10경기 7승 3패를 기록하였으며, 두산 타선은 최근 5경기 평균 5.4득점으로 활발합니다. 다만 LG 외국인 타자의 최근 5경기 타율 .380은 주요 위협 변수입니다.",
    "home_starter": {
      "player_id": 10,
      "name": "곽빈",
      "throw_hand": "RIGHT",
      "recent_5g_era": 1.80,
      "recent_5g_whip": 0.95,
      "recent_5g_strikeouts": 28
    },
    "away_starter": {
      "player_id": 25,
      "name": "임찬규",
      "throw_hand": "LEFT",
      "recent_5g_era": 3.45,
      "recent_5g_whip": 1.22,
      "recent_5g_strikeouts": 19
    },
    "updated_at": "2025-05-10T20:00:00+09:00",
    "is_final": true
  }
}
```

**Response 예외**

| 상태 코드 | 설명 |
|----------|------|
| 200 | 성공 |
| 404 | 해당 game_id 없음 |
| 500 | 서버 내부 오류 |

---

### 4-3. 팀 통계

```
GET /teams/{team_id}/stats
```

**설명**: 특정 팀의 최근 폼 통계 반환 (최근 10경기 기준).

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| team_id | integer | Y | 팀 ID |

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| last_n | integer | N | 10 | 최근 N경기 기준 (최대 30) |

**Response 200**

```json
{
  "team": {
    "id": 1,
    "name": "두산 베어스",
    "short_name": "두산",
    "home_stadium": "잠실야구장",
    "logo_url": "https://..."
  },
  "recent_stats": {
    "last_n_games": 10,
    "wins": 7,
    "losses": 3,
    "win_rate": 0.700,
    "avg_runs_scored": 5.4,
    "avg_ops": 0.812,
    "avg_batting_avg": 0.285,
    "home_record": { "wins": 4, "losses": 1 },
    "away_record": { "wins": 3, "losses": 2 },
    "streak": "W3"
  },
  "updated_at": "2025-05-10T09:00:00+09:00"
}
```

---

### 4-4. 선발 투수 통계

```
GET /pitchers/{player_id}/stats
```

**설명**: 특정 선발 투수의 최근 경기 기록 반환.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| player_id | integer | Y | 선수 ID |

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| last_n | integer | N | 5 | 최근 N경기 기준 (최대 10) |

**Response 200**

```json
{
  "player": {
    "id": 10,
    "name": "곽빈",
    "team": { "id": 1, "name": "두산 베어스" },
    "throw_hand": "RIGHT",
    "is_foreign": false
  },
  "season_stats": {
    "era": 2.10,
    "whip": 1.05,
    "wins": 5,
    "losses": 2,
    "strikeouts": 68,
    "innings_pitched": 51.3
  },
  "recent_games": [
    {
      "game_id": 1,
      "game_date": "2025-05-07",
      "opponent_team": "KIA 타이거즈",
      "innings_pitched": 7.0,
      "hits_allowed": 3,
      "earned_runs": 0,
      "strikeouts": 9,
      "era_game": 0.00,
      "whip_game": 0.86
    }
  ],
  "recent_5g_avg": {
    "era": 1.80,
    "whip": 0.95,
    "strikeouts_per_game": 8.2,
    "innings_pitched_avg": 6.4
  }
}
```

---

### 4-5. 팀 목록

```
GET /teams
```

**설명**: KBO 10개 구단 전체 목록.

**Response 200**

```json
{
  "teams": [
    {
      "id": 1,
      "name": "두산 베어스",
      "short_name": "두산",
      "logo_url": "https://...",
      "home_stadium": "잠실야구장"
    }
  ],
  "total": 10
}
```

---

### 4-6. [Admin] 예측 수동 트리거

```
POST /admin/predictions/trigger
```

**설명**: 특정 경기 또는 오늘 전체 경기 예측을 수동으로 실행. 스케줄러 오류 대비용.

**Request Body**

```json
{
  "game_id": 1,        // 특정 경기 (null이면 오늘 전체)
  "force": true        // 이미 예측 있어도 강제 재실행
}
```

**Response 202**

```json
{
  "message": "Prediction task queued",
  "game_id": 1,
  "queued_at": "2025-05-10T15:30:00+09:00"
}
```

---

### 4-7. API 공통 에러 형식

```json
{
  "error": {
    "code": "GAME_NOT_FOUND",
    "message": "해당 경기를 찾을 수 없습니다.",
    "status": 404
  }
}
```

---

## 5. 파일 구조도

### 5-1. 전체 프로젝트 구조

```
kbo-predict/
├── backend/                    # FastAPI 백엔드
├── frontend/                   # Next.js 프론트엔드
├── docker-compose.yml          # 로컬 개발 환경 (PostgreSQL + Redis)
├── .env.example
└── README.md
```

---

### 5-2. 백엔드 파일 구조 (FastAPI)

```
backend/
├── app/
│   ├── main.py                     # FastAPI 앱 초기화, 라우터 등록
│   ├── config.py                   # 환경변수 설정 (pydantic-settings)
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # v1 라우터 통합
│   │       ├── games.py            # GET /games/today, GET /games/{id}/prediction
│   │       ├── teams.py            # GET /teams, GET /teams/{id}/stats
│   │       ├── pitchers.py         # GET /pitchers/{id}/stats
│   │       └── admin.py            # POST /admin/predictions/trigger
│   │
│   ├── models/
│   │   ├── db/                     # SQLAlchemy ORM 모델
│   │   │   ├── base.py
│   │   │   ├── team.py
│   │   │   ├── player.py
│   │   │   ├── game.py
│   │   │   ├── prediction.py
│   │   │   ├── pitcher_stat.py
│   │   │   └── team_stat.py
│   │   └── schemas/                # Pydantic 요청/응답 스키마
│   │       ├── game.py
│   │       ├── team.py
│   │       ├── pitcher.py
│   │       └── prediction.py
│   │
│   ├── services/                   # 비즈니스 로직
│   │   ├── game_service.py         # 오늘의 경기 조회 + 캐싱
│   │   ├── prediction_service.py   # 예측 파이프라인 오케스트레이션
│   │   ├── team_service.py         # 팀 통계 집계
│   │   ├── pitcher_service.py      # 투수 통계 집계
│   │   └── ai_reasoning_service.py # Claude API 근거 생성
│   │
│   ├── ml/                         # ML/DL 모델
│   │   ├── feature_engineering.py  # 피처 추출 및 전처리
│   │   ├── xgboost_model.py        # XGBoost Stage 1 예측
│   │   ├── pytorch_model.py        # PyTorch/LSTM Stage 2 예측
│   │   ├── ensemble.py             # 앙상블 (가중 평균)
│   │   └── artifacts/              # 학습된 모델 파일
│   │       ├── xgboost_v1.pkl
│   │       └── pytorch_v1.pt
│   │
│   ├── crawler/                    # 데이터 수집
│   │   ├── base_crawler.py         # 공통 크롤러 베이스 (요청 간격, User-Agent)
│   │   ├── statiz_crawler.py       # statiz.co.kr 경기 결과/통계
│   │   ├── naver_crawler.py        # 네이버스포츠 선발 투수
│   │   ├── weather_client.py       # 기상청 API
│   │   └── odds_client.py          # Odds API 배당률
│   │
│   ├── scheduler/
│   │   ├── tasks.py                # APScheduler 태스크 정의
│   │   └── runner.py               # 스케줄러 시작/중지
│   │
│   ├── db/
│   │   ├── database.py             # SQLAlchemy 엔진, 세션
│   │   ├── redis_client.py         # Redis 연결 및 헬퍼
│   │   └── migrations/             # Alembic 마이그레이션
│   │       └── versions/
│   │
│   └── utils/
│       ├── logger.py               # 로깅 설정
│       ├── cache.py                # Redis 캐싱 데코레이터
│       └── exceptions.py           # 커스텀 예외
│
├── tests/
│   ├── test_api/
│   │   ├── test_games.py
│   │   └── test_teams.py
│   ├── test_ml/
│   │   └── test_xgboost.py
│   └── test_crawler/
│       └── test_statiz.py
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── alembic.ini
```

---

### 5-3. 프론트엔드 파일 구조 (Next.js 14 App Router)

```
frontend/
├── app/                            # App Router
│   ├── layout.tsx                  # 루트 레이아웃 (공통 헤더/네비)
│   ├── page.tsx                    # HOME001 — 오늘의 경기 예측 목록
│   ├── games/
│   │   └── [id]/
│   │       └── page.tsx            # GAME001 — 경기 상세 예측
│   ├── stats/
│   │   └── page.tsx                # STAT001 — 팀/투수 통계
│   ├── loading.tsx                 # 전역 로딩 UI
│   ├── error.tsx                   # 전역 에러 UI
│   └── not-found.tsx               # 404 페이지
│
├── components/
│   ├── layout/
│   │   ├── Header.tsx              # 상단 네비게이션
│   │   └── Footer.tsx
│   ├── game/
│   │   ├── GameCard.tsx            # 경기 예측 카드 (HOME002)
│   │   ├── ProbabilityBar.tsx      # 승리 확률 바 시각화
│   │   ├── ConfidenceBadge.tsx     # 신뢰도 별점 (HIGH/MEDIUM/LOW)
│   │   └── AiReasoning.tsx         # AI 근거 텍스트 박스
│   ├── pitcher/
│   │   ├── PitcherCard.tsx         # 선발 투수 카드 (STAT003)
│   │   └── PitcherStatTable.tsx    # 투수 최근 기록 테이블
│   └── stats/
│       ├── TeamStatTable.tsx       # 팀 통계 테이블 (STAT002)
│       └── TeamSelector.tsx        # 팀 선택 드롭다운
│
├── lib/
│   ├── api/
│   │   ├── client.ts               # Axios/Fetch 클라이언트 설정
│   │   ├── games.ts                # 경기 관련 API 호출 함수
│   │   ├── teams.ts                # 팀 관련 API 호출 함수
│   │   └── pitchers.ts             # 투수 관련 API 호출 함수
│   └── utils/
│       ├── date.ts                 # KST 날짜 포맷 유틸
│       └── format.ts               # 확률/수치 포맷 유틸
│
├── types/
│   └── index.ts                    # 공통 타입 정의 (Game, Team, Prediction 등)
│
├── public/
│   └── teams/                      # 팀 로고 이미지
│
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.local.example
```

---

### 5-4. 파일/디렉토리 일괄 생성 명령어

아래 명령어를 프로젝트 루트에서 실행하면 백엔드와 프론트엔드 디렉토리 구조가 한 번에 생성됩니다.

```bash
#!/bin/bash
# ============================================================
# KBO 야구 승부예측 AI — 프로젝트 구조 생성 스크립트
# 사용법: bash setup.sh
# ============================================================

PROJECT_ROOT="kbo-predict"
mkdir -p "$PROJECT_ROOT" && cd "$PROJECT_ROOT"

# ── 백엔드 디렉토리 ──────────────────────────────────────────
BACKEND_DIRS=(
  "backend/app/api/v1"
  "backend/app/models/db"
  "backend/app/models/schemas"
  "backend/app/services"
  "backend/app/ml/artifacts"
  "backend/app/crawler"
  "backend/app/scheduler"
  "backend/app/db/migrations/versions"
  "backend/app/utils"
  "backend/tests/test_api"
  "backend/tests/test_ml"
  "backend/tests/test_crawler"
)

for dir in "${BACKEND_DIRS[@]}"; do
  mkdir -p "$dir"
done

# 백엔드 파일 생성
BACKEND_FILES=(
  "backend/app/main.py"
  "backend/app/config.py"
  "backend/app/api/v1/__init__.py"
  "backend/app/api/v1/router.py"
  "backend/app/api/v1/games.py"
  "backend/app/api/v1/teams.py"
  "backend/app/api/v1/pitchers.py"
  "backend/app/api/v1/admin.py"
  "backend/app/models/db/base.py"
  "backend/app/models/db/team.py"
  "backend/app/models/db/player.py"
  "backend/app/models/db/game.py"
  "backend/app/models/db/prediction.py"
  "backend/app/models/db/pitcher_stat.py"
  "backend/app/models/db/team_stat.py"
  "backend/app/models/schemas/game.py"
  "backend/app/models/schemas/team.py"
  "backend/app/models/schemas/pitcher.py"
  "backend/app/models/schemas/prediction.py"
  "backend/app/services/game_service.py"
  "backend/app/services/prediction_service.py"
  "backend/app/services/team_service.py"
  "backend/app/services/pitcher_service.py"
  "backend/app/services/ai_reasoning_service.py"
  "backend/app/ml/feature_engineering.py"
  "backend/app/ml/xgboost_model.py"
  "backend/app/ml/pytorch_model.py"
  "backend/app/ml/ensemble.py"
  "backend/app/crawler/base_crawler.py"
  "backend/app/crawler/statiz_crawler.py"
  "backend/app/crawler/naver_crawler.py"
  "backend/app/crawler/weather_client.py"
  "backend/app/crawler/odds_client.py"
  "backend/app/scheduler/tasks.py"
  "backend/app/scheduler/runner.py"
  "backend/app/db/database.py"
  "backend/app/db/redis_client.py"
  "backend/app/utils/logger.py"
  "backend/app/utils/cache.py"
  "backend/app/utils/exceptions.py"
  "backend/tests/test_api/test_games.py"
  "backend/tests/test_api/test_teams.py"
  "backend/tests/test_ml/test_xgboost.py"
  "backend/tests/test_crawler/test_statiz.py"
  "backend/requirements.txt"
  "backend/Dockerfile"
  "backend/.env.example"
  "backend/alembic.ini"
)

for file in "${BACKEND_FILES[@]}"; do
  touch "$file"
done

# ── 프론트엔드 디렉토리 ──────────────────────────────────────
FRONTEND_DIRS=(
  "frontend/app/games/[id]"
  "frontend/app/stats"
  "frontend/components/layout"
  "frontend/components/game"
  "frontend/components/pitcher"
  "frontend/components/stats"
  "frontend/lib/api"
  "frontend/lib/utils"
  "frontend/types"
  "frontend/public/teams"
)

for dir in "${FRONTEND_DIRS[@]}"; do
  mkdir -p "$dir"
done

# 프론트엔드 파일 생성
FRONTEND_FILES=(
  "frontend/app/layout.tsx"
  "frontend/app/page.tsx"
  "frontend/app/loading.tsx"
  "frontend/app/error.tsx"
  "frontend/app/not-found.tsx"
  "frontend/app/games/[id]/page.tsx"
  "frontend/app/stats/page.tsx"
  "frontend/components/layout/Header.tsx"
  "frontend/components/layout/Footer.tsx"
  "frontend/components/game/GameCard.tsx"
  "frontend/components/game/ProbabilityBar.tsx"
  "frontend/components/game/ConfidenceBadge.tsx"
  "frontend/components/game/AiReasoning.tsx"
  "frontend/components/pitcher/PitcherCard.tsx"
  "frontend/components/pitcher/PitcherStatTable.tsx"
  "frontend/components/stats/TeamStatTable.tsx"
  "frontend/components/stats/TeamSelector.tsx"
  "frontend/lib/api/client.ts"
  "frontend/lib/api/games.ts"
  "frontend/lib/api/teams.ts"
  "frontend/lib/api/pitchers.ts"
  "frontend/lib/utils/date.ts"
  "frontend/lib/utils/format.ts"
  "frontend/types/index.ts"
  "frontend/next.config.ts"
  "frontend/tailwind.config.ts"
  "frontend/tsconfig.json"
  "frontend/package.json"
  "frontend/.env.local.example"
)

for file in "${FRONTEND_FILES[@]}"; do
  touch "$file"
done

# ── 루트 공통 파일 ──────────────────────────────────────────
touch docker-compose.yml .env.example README.md

echo ""
echo "✅ 프로젝트 구조 생성 완료!"
echo ""
echo "다음 단계:"
echo "  1. cd kbo-predict"
echo "  2. cp .env.example .env  (환경변수 설정)"
echo "  3. docker-compose up -d  (PostgreSQL + Redis 실행)"
echo "  4. cd backend && pip install -r requirements.txt"
echo "  5. cd frontend && npm install"
```

```bash
# 스크립트 실행 방법
chmod +x setup.sh
bash setup.sh
```

---

### 5-5. 2주 스프린트 계획 (P0 MVP)

| 주차 | 일차 | 담당 영역 | 주요 작업 | 완료 기준 |
|------|------|-----------|-----------|-----------|
| 1주차 | Day 1 | 인프라/데이터 | 프로젝트 셋업, Docker 환경 구성, DB 스키마 생성, 크롤러 기반 구축 | `setup.sh` 실행 후 PostgreSQL+Redis 동작 |
| 1주차 | Day 2 | 데이터 수집 | statiz 크롤러 완성, 최근 3시즌 경기 결과 + 팀 통계 수집 | DB에 3시즌 경기 데이터 저장 완료 |
| 1주차 | Day 3 | 데이터 수집 | 선발 투수(네이버) 크롤러, 날씨 API, Odds API 연동 | 모든 데이터 소스 수집 동작 확인 |
| 1주차 | Day 4 | ML — Stage 1 | 피처 엔지니어링 + XGBoost 학습 + 백테스팅 | 백테스팅 정확도 55% 이상 |
| 1주차 | Day 5 | ML — Stage 1 | XGBoost 하이퍼파라미터 튜닝 + 모델 저장 (.pkl) | 목표 정확도 58% 달성 |
| 1주차 | Day 6 | ML — Stage 2 | PyTorch TabTransformer/LSTM 구현 시작 | 모델 아키텍처 코드 완성 |
| 1주차 | Day 7 | ML — Stage 2 | PyTorch Fine-tuning + Stage1 앙상블 | 앙상블 예측값 생성 동작 |
| 2주차 | Day 8 | AI API | Claude API 연동 + 근거 생성 프롬프트 작성 | 자연어 근거 텍스트 생성 동작 |
| 2주차 | Day 9 | 백엔드 | FastAPI 라우터 + 서비스 레이어 구현 | `/games/today`, `/games/{id}/prediction` API 응답 정상 |
| 2주차 | Day 10 | 백엔드 | 팀·투수 API + Redis 캐싱 + APScheduler 연동 | 스케줄러 자동 실행, 캐시 TTL 동작 |
| 2주차 | Day 11 | 프론트엔드 | Next.js 앱 초기화 + 홈 페이지 (GameCard, ProbabilityBar) | 오늘의 경기 카드 목록 렌더링 |
| 2주차 | Day 12 | 프론트엔드 | 경기 상세 페이지 + 통계 페이지 완성 | GAME001, STAT001 화면 완성 |
| 2주차 | Day 13 | 배포 | Railway/EC2 배포 설정 (Dockerfile, 환경변수) | 공개 URL 접속 가능 |
| 2주차 | Day 14 | QA / 마무리 | 전체 플로우 E2E 테스트, 버그 수정, README 작성 | 서비스 정상 운영 확인 |

---

> **설계 문서 작성일**: 2025년  
> **문서 버전**: v1.0 (P0 MVP)  
> **다음 단계**: 와이어프레임 작성 → 컴포넌트 개발 시작
