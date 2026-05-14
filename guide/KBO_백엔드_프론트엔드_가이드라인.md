# ⚾ KBO 야구 승부예측 AI — 백엔드 & 프론트엔드 개발 가이드라인 (A to Z)

> **대상 독자**: 개발을 처음 시작하는 팀원도 이 문서 하나로 처음부터 끝까지 따라할 수 있도록 작성되었습니다.  
> **담당 파트**: 백엔드(FastAPI) + 프론트엔드(Next.js 14)  
> **MVP 범위**: P0 — 오늘의 경기 예측 / 예측 상세 보기 / 팀·선수 통계 보기

---

## 목차

1. [프로젝트 요약](#1-프로젝트-요약)
   - 1.1 프로젝트 개요
   - 1.2 사용 기술 스택 및 설치 방법
   - 1.3 시스템 아키텍처 요약
   - 1.4 데이터베이스 설계 요약
   - 1.5 API 명세 요약
2. [세팅](#2-세팅)
   - 2.1 도커 세팅 및 데이터베이스 SQL 적용 이후 실행까지
   - 2.2 깃 협업 가이드
3. [개발](#3-개발)
   - 3.1.1 백엔드 (FastAPI)
   - 3.1.2 프론트엔드 (Next.js 14)
   - 3.2 협업 가이드
4. [일정 및 계획표](#4-일정-및-계획표)
5. [배포 가이드](#5-배포-가이드-docker--ec2)
6. [최종 체크리스트](#6-최종-체크리스트)

---

## 1. 프로젝트 요약

### 1.1 프로젝트 개요

#### 서비스 한줄 소개

> **KBO 야구 경기의 승리 확률을 AI가 예측해주는 서비스** — XGBoost + LSTM 앙상블 모델과 Claude AI 자연어 근거를 결합해 당일 전체 경기 예측을 제공합니다.

#### 핵심 기능 목록 (P0 범위)

| 코드 | 화면명 | 기능 설명 |
|------|--------|-----------|
| HOME001 | 홈 화면 | 당일 KBO 전경기 예측 카드 목록 노출. 경기가 없는 날은 안내 문구 표시 |
| HOME002 | 오늘의 경기 목록 | 홈팀/원정팀 로고·이름, 승리 확률 바, 신뢰도 배지, 선발 투수명·ERA, 예측 업데이트 시각 |
| GAME001 | 경기 상세 | 특정 경기의 예측 상세 페이지 (`/games/[id]`) |
| GAME002 | 승리 확률 상세 | XGBoost 단독 / LSTM 앙상블 결과 수치 + 시각화 바 병렬 표시 |
| GAME003 | AI 예측 근거 | Claude API가 생성한 자연어 예측 근거 (3~5줄). 선발 투수 분석·팀 폼·핵심 변수 포함 |
| STAT001 | 통계 허브 | 팀별·선수별 통계 페이지 (`/stats`) |
| STAT002 | 팀 통계 | 10개 KBO 팀 최근 10경기 승률, OPS, 평균 득점. 홈/원정 탭 구분 |
| STAT003 | 선발 투수 정보 | 당일 선발 예정 투수 카드. 최근 5경기 ERA·WHIP·탈삼진, 상대 타선 대비 성적 |

---

### 1.2 사용 기술 스택 및 버전, 설치 방법

#### 기술 스택

| 영역 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **백엔드** | FastAPI | 0.115.x | REST API 서버 |
| | SQLAlchemy | 2.0.x | ORM (DB 모델 관리) |
| | Alembic | 1.13.x | DB 마이그레이션 |
| | Pydantic | 2.x | 요청/응답 스키마 검증 |
| | APScheduler | 3.10.x | 자동 스케줄링 (크롤링 트리거) |
| | Uvicorn | 0.29.x | ASGI 서버 |
| | Anthropic Python SDK | 0.26.x | Claude API 연동 |
| **프론트엔드** | Next.js | 14.x (App Router) | React 풀스택 프레임워크 |
| | React | 18.x | UI 라이브러리 |
| | TypeScript | 5.x | 타입 안전 JavaScript |
| | Tailwind CSS | 3.x | 유틸리티 CSS 프레임워크 |
| | Axios | 1.x | HTTP 클라이언트 |
| **데이터베이스** | PostgreSQL | 15.x | 메인 데이터베이스 |
| | Redis | 7.x | 예측 결과 캐싱 (TTL 30분) |
| **인프라** | Docker | 26.x | 로컬 개발 환경 컨테이너화 |
| | Docker Compose | 2.x | 멀티 컨테이너 관리 |

#### 설치 필수 도구 (먼저 설치하세요)

**1. Git 설치**
```bash
# macOS (Homebrew)
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows → https://git-scm.com/download/win 에서 설치
```

**2. Docker Desktop 설치**
- [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) 에서 OS에 맞게 다운로드 및 설치
- 설치 후 Docker Desktop 실행 (고래 아이콘이 상단 바에 뜨면 정상)

**3. Python 3.11 설치**
```bash
# macOS
brew install python@3.11

# Ubuntu
sudo apt-get install python3.11 python3.11-venv python3.11-pip

# 버전 확인
python3 --version   # Python 3.11.x
```

**4. Node.js 20 LTS 설치**
- [https://nodejs.org](https://nodejs.org) 에서 `LTS` 버전 다운로드 및 설치
```bash
# 설치 확인
node --version   # v20.x.x
npm --version    # 10.x.x
```

---

### 1.3 시스템 아키텍처 요약

```
[사용자 브라우저]
      │  HTTPS
      ▼
[Next.js 14 프론트엔드]  ← Vercel 또는 Railway 배포
      │  REST API (JSON)
      ▼
[FastAPI 백엔드]          ← Docker / EC2
      ├── APScheduler (자동 스케줄링)
      │     ├── 매일 06:00 — 크롤링 결과 수집
      │     ├── 매일 18:00 — 선발 투수 + 날씨 수집
      │     └── 매일 19:30 — ML 추론 + Claude AI 근거 생성
      ├── ML/AI 모듈 (XGBoost + LSTM 앙상블)
      └── Claude API (예측 근거 자연어 생성)
            │
      ┌─────┴─────┐
      ▼           ▼
[PostgreSQL]   [Redis]
 (영구 저장)   (캐싱 TTL 30분~1시간)
```

**핵심 데이터 흐름:**
1. 크롤러가 외부 소스(statiz, KBO 공식, 네이버스포츠)에서 데이터 수집 → PostgreSQL 저장
2. APScheduler가 19:30에 ML 추론 실행 → XGBoost + LSTM 앙상블 → Claude API 근거 생성 → DB 저장
3. 사용자가 접속 → FastAPI가 Redis 캐시 우선 조회 → 없으면 DB 조회 → Next.js로 응답

---

### 1.4 데이터베이스 설계 요약

#### 핵심 테이블 관계도

```
teams (10개 구단)
  ├──< players (선수 정보, 투수 중심)
  ├──< games (경기 일정 및 결과)  [홈팀 / 원정팀 각각 참조]
  │     ├──< game_predictions (AI 예측 결과)
  │     ├──< pitcher_game_stats (투수 경기별 기록)
  │     └──< team_game_stats (팀 경기별 타선 기록)
  └──< team_daily_snapshots (일별 팀 순위 스냅샷 — ML 학습용)
```

#### 주요 테이블 한줄 설명

| 테이블 | 설명 |
|--------|------|
| `teams` | KBO 10개 구단 기본 정보 |
| `players` | 선수 정보 (MVP는 투수 중심) |
| `games` | 경기 일정, 점수, 상태(예정/진행/완료) |
| `game_predictions` | XGBoost + LSTM 예측 확률, Claude AI 근거 텍스트, 신뢰도 |
| `pitcher_game_stats` | 선발 투수 경기별 ERA, WHIP, 탈삼진 |
| `team_game_stats` | 팀 경기별 득점, OPS, 타율 |
| `team_daily_snapshots` | 일별 팀 순위 스냅샷 (AI 파트에서 생성, 백엔드에서 조회) |
| `crawl_logs` | 크롤링 실행 이력 및 에러 기록 |

---

### 1.5 API 명세 요약

**Base URL**: `http://localhost:8000/api/v1` (로컬) / `https://api.kbo-predict.com/api/v1` (배포)

#### 경기 / 예측 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/games/today` | 오늘의 경기 예측 전체 목록 (Redis 캐싱) |
| GET | `/games/{game_id}/prediction` | 특정 경기 예측 상세 + AI 근거 |
| POST | `/admin/predictions/trigger` | 예측 수동 트리거 (스케줄러 오류 대비) |

#### 팀 / 투수 통계 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/teams` | KBO 10개 구단 목록 |
| GET | `/teams/{team_id}/stats` | 특정 팀 최근 10경기 통계 |
| GET | `/pitchers/{player_id}/stats` | 특정 투수 최근 5경기 기록 |

#### 공통 에러 응답 형식

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

## 2. 세팅

### 2.1 도커 세팅 및 데이터베이스 SQL 적용 이후 실행까지

> **이 단계는 팀 전체가 동일하게 진행합니다. 팀장이 먼저 설정 후 팀원과 공유합니다.**

#### Step 1. 프로젝트 루트 구조 생성

아래 명령어를 터미널에 붙여넣어 실행하세요.

```bash
# 프로젝트 폴더 생성
mkdir kbo-predict && cd kbo-predict

# ── 백엔드 디렉토리 ──
mkdir -p backend/app/api/v1
mkdir -p backend/app/models/db
mkdir -p backend/app/models/schemas
mkdir -p backend/app/services
mkdir -p backend/app/ml/artifacts
mkdir -p backend/app/crawler
mkdir -p backend/app/scheduler
mkdir -p backend/app/db/migrations/versions
mkdir -p backend/app/utils
mkdir -p backend/tests/test_api
mkdir -p backend/tests/test_ml

# ── 프론트엔드 디렉토리 ──
mkdir -p frontend/app/games/\[id\]
mkdir -p frontend/app/stats
mkdir -p frontend/components/layout
mkdir -p frontend/components/game
mkdir -p frontend/components/pitcher
mkdir -p frontend/components/stats
mkdir -p frontend/lib/api
mkdir -p frontend/lib/utils
mkdir -p frontend/types
mkdir -p frontend/public/teams

echo "✅ 폴더 생성 완료!"
```

#### Step 2. docker-compose.yml 작성

프로젝트 루트(`kbo-predict/`)에 `docker-compose.yml` 파일을 생성하세요.

```yaml
# kbo-predict/docker-compose.yml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    container_name: kbo_postgres
    restart: always
    environment:
      POSTGRES_DB: kbo_predict
      POSTGRES_USER: kbo_user
      POSTGRES_PASSWORD: kbo_password123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql  # 초기 SQL 자동 실행
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kbo_user -d kbo_predict"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: kbo_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:
```

#### Step 3. DB 초기화 SQL 파일 작성

`kbo-predict/db/init.sql` 파일을 생성하세요. **이 파일이 Docker 실행 시 자동으로 적용됩니다.**

```bash
mkdir -p db
```

`db/init.sql` 파일을 만들고 아래 내용을 붙여넣으세요:

```sql
-- ============================================================
-- KBO 야구 승부예측 AI — 초기 DB 스키마
-- Docker 컨테이너 최초 실행 시 자동 적용됩니다.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. teams (팀 정보)
CREATE TABLE IF NOT EXISTS teams (
  id            SERIAL PRIMARY KEY,
  name          VARCHAR(50)  NOT NULL UNIQUE,
  short_name    VARCHAR(20)  NOT NULL UNIQUE,
  logo_url      VARCHAR(255),
  home_stadium  VARCHAR(100),
  is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 2. players (선수 정보)
CREATE TABLE IF NOT EXISTS players (
  id          SERIAL PRIMARY KEY,
  team_id     INT          NOT NULL REFERENCES teams(id),
  name        VARCHAR(50)  NOT NULL,
  position    VARCHAR(20)  NOT NULL,
  throw_hand  VARCHAR(10),
  bat_hand    VARCHAR(10),
  is_foreign  BOOLEAN      NOT NULL DEFAULT FALSE,
  is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

-- 3. games (경기 일정 및 결과)
CREATE TABLE IF NOT EXISTS games (
  id              SERIAL PRIMARY KEY,
  home_team_id    INT         NOT NULL REFERENCES teams(id),
  away_team_id    INT         NOT NULL REFERENCES teams(id),
  scheduled_at    TIMESTAMP   NOT NULL,
  stadium         VARCHAR(100),
  home_score      SMALLINT,
  away_score      SMALLINT,
  status          VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
  season          SMALLINT    NOT NULL,
  created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_different_teams CHECK (home_team_id <> away_team_id)
);

CREATE INDEX IF NOT EXISTS idx_games_scheduled_at ON games(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_date_status ON games(DATE(scheduled_at), status);

-- 4. game_predictions (예측 결과)
CREATE TABLE IF NOT EXISTS game_predictions (
  id                        SERIAL     PRIMARY KEY,
  game_id                   INT        NOT NULL REFERENCES games(id),
  home_win_prob             DECIMAL(5,4) NOT NULL,
  away_win_prob             DECIMAL(5,4) NOT NULL,
  confidence_level          VARCHAR(10) NOT NULL DEFAULT 'MEDIUM',
  xgboost_home_prob         DECIMAL(5,4),
  pytorch_home_prob         DECIMAL(5,4),
  ensemble_weight_xgb       DECIMAL(3,2) DEFAULT 0.60,
  ai_reasoning              TEXT,
  home_starter_id           INT REFERENCES players(id),
  away_starter_id           INT REFERENCES players(id),
  is_final                  BOOLEAN    NOT NULL DEFAULT FALSE,
  model_version             VARCHAR(20),
  predicted_at              TIMESTAMP  NOT NULL DEFAULT NOW(),
  actual_result             VARCHAR(10),
  CONSTRAINT chk_prob_sum CHECK (
    ABS((home_win_prob + away_win_prob) - 1.0) < 0.0001
  )
);

CREATE INDEX IF NOT EXISTS idx_predictions_game_id ON game_predictions(game_id);
CREATE INDEX IF NOT EXISTS idx_predictions_is_final ON game_predictions(game_id, is_final);

-- 5. pitcher_game_stats (투수 경기별 기록)
CREATE TABLE IF NOT EXISTS pitcher_game_stats (
  id               SERIAL     PRIMARY KEY,
  player_id        INT        NOT NULL REFERENCES players(id),
  game_id          INT        NOT NULL REFERENCES games(id),
  is_starter       BOOLEAN    NOT NULL DEFAULT TRUE,
  innings_pitched  DECIMAL(4,1),
  hits_allowed     SMALLINT,
  earned_runs      SMALLINT,
  walks            SMALLINT,
  strikeouts       SMALLINT,
  era              DECIMAL(5,2),
  whip             DECIMAL(5,2),
  created_at       TIMESTAMP  NOT NULL DEFAULT NOW(),
  UNIQUE(player_id, game_id)
);

-- 6. team_game_stats (팀 경기별 타선 기록)
CREATE TABLE IF NOT EXISTS team_game_stats (
  id            SERIAL     PRIMARY KEY,
  team_id       INT        NOT NULL REFERENCES teams(id),
  game_id       INT        NOT NULL REFERENCES games(id),
  is_home       BOOLEAN    NOT NULL,
  runs_scored   SMALLINT,
  hits          SMALLINT,
  home_runs     SMALLINT,
  ops           DECIMAL(5,3),
  batting_avg   DECIMAL(4,3),
  created_at    TIMESTAMP  NOT NULL DEFAULT NOW(),
  UNIQUE(team_id, game_id)
);

-- 7. team_daily_snapshots (일별 팀 순위 스냅샷 — AI 파트에서 채움)
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
  streak_type     VARCHAR(10),
  streak_count    SMALLINT,
  created_at      TIMESTAMP DEFAULT NOW(),
  UNIQUE(team_id, snapshot_date)
);

-- 8. crawl_logs (크롤링 이력)
CREATE TABLE IF NOT EXISTS crawl_logs (
  id                SERIAL     PRIMARY KEY,
  source            VARCHAR(50) NOT NULL,
  task_type         VARCHAR(50) NOT NULL,
  status            VARCHAR(20) NOT NULL,
  records_collected INT         NOT NULL DEFAULT 0,
  error_message     TEXT,
  crawled_at        TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- 9. player_season_stats (선수 시즌 통계 — AI 파트에서 채움)
CREATE TABLE IF NOT EXISTS player_season_stats (
  id              SERIAL PRIMARY KEY,
  player_id       INT NOT NULL REFERENCES players(id),
  season          SMALLINT NOT NULL,
  avg             DECIMAL(4,3),
  obp             DECIMAL(4,3),
  slg             DECIMAL(4,3),
  ops             DECIMAL(5,3),
  hr              SMALLINT,
  rbi             SMALLINT,
  sb              SMALLINT,
  war_batter      DECIMAL(4,2),
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

-- ============================================================
-- 초기 데이터 — KBO 10개 구단
-- ============================================================
INSERT INTO teams (name, short_name, home_stadium) VALUES
  ('두산 베어스',   '두산',   '잠실야구장'),
  ('LG 트윈스',    'LG',     '잠실야구장'),
  ('키움 히어로즈', '키움',   '고척스카이돔'),
  ('KT 위즈',      'KT',     '수원KT위즈파크'),
  ('SSG 랜더스',   'SSG',    '인천SSG랜더스필드'),
  ('NC 다이노스',  'NC',     '창원NC파크'),
  ('KIA 타이거즈', 'KIA',    '광주-기아챔피언스필드'),
  ('롯데 자이언츠', '롯데',   '사직야구장'),
  ('삼성 라이온즈', '삼성',   '대구삼성라이온즈파크'),
  ('한화 이글스',  '한화',    '한화생명이글스파크')
ON CONFLICT DO NOTHING;
```

#### Step 4. Docker 실행 및 DB 확인

```bash
# kbo-predict/ 루트에서 실행
docker compose up -d

# 실행 상태 확인 (모두 running 이어야 합니다)
docker compose ps

# 예상 출력:
# NAME           STATUS    PORTS
# kbo_postgres   running   0.0.0.0:5432->5432/tcp
# kbo_redis      running   0.0.0.0:6379->6379/tcp

# DB 접속 테스트 (teams 테이블 확인)
docker exec -it kbo_postgres psql -U kbo_user -d kbo_predict -c "SELECT name FROM teams;"

# 예상 출력: 두산 베어스, LG 트윈스 등 10개 팀 이름
```

> **❗ 주의사항**: Docker Desktop이 실행 중인지 먼저 확인하세요. 종료되어 있으면 `Error response from daemon` 에러가 납니다.

#### Step 5. 백엔드 Python 환경 설정

```bash
cd backend

# 가상환경 생성 (Python 버전 격리)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# (venv) 표시가 뜨면 성공!
```

`backend/requirements.txt` 파일을 생성하고 아래 내용을 붙여넣으세요:

```txt
# Web Framework
fastapi==0.115.5
uvicorn[standard]==0.29.0
python-multipart==0.0.9

# Database
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9

# Caching
redis==5.1.0

# Validation
pydantic==2.9.2
pydantic-settings==2.5.2

# Scheduler
apscheduler==3.10.4

# AI API
anthropic==0.26.1

# HTTP
httpx==0.27.2
requests==2.32.3

# Utilities
python-dotenv==1.0.1
loguru==0.7.2
```

```bash
pip install -r requirements.txt

# 설치 확인
python -c "import fastapi; print(fastapi.__version__)"   # 0.115.5
```

#### Step 6. 백엔드 환경변수 설정

`backend/.env` 파일 생성:

```bash
# .env.example을 복사해서 .env 생성
cp .env.example .env
```

`backend/.env` 내용:

```env
# ── 데이터베이스 ──
DATABASE_URL=postgresql://kbo_user:kbo_password123@localhost:5432/kbo_predict

# ── Redis ──
REDIS_URL=redis://localhost:6379/0

# ── Claude API ──
# https://console.anthropic.com 에서 발급
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxx

# ── ML 모델 경로 ──
XGBOOST_ARTIFACT_PATH=app/ml/artifacts/kbo_xgb_v1.pkl
LSTM_ARTIFACT_PATH=app/ml/artifacts/kbo_lstm_v1.pt
MODEL_VERSION=v1.0-xgb+lstm

# ── 앱 설정 ──
APP_ENV=development
DEBUG=True
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:3000
```

> **🔒 중요**: `.env` 파일은 **절대 Git에 올리면 안 됩니다!** (`.gitignore`에 이미 포함되어 있습니다)

#### Step 7. 백엔드 서버 실행

```bash
# backend/ 폴더에서 실행
cd backend
source venv/bin/activate

# 개발 서버 실행 (코드 변경 시 자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 브라우저에서 확인
# http://localhost:8000/docs  → Swagger UI (API 문서 자동 생성)
# http://localhost:8000/api/v1/teams  → 팀 목록 조회 테스트
```

#### Step 8. 프론트엔드 Next.js 프로젝트 초기화

```bash
cd frontend

# Next.js 14 프로젝트 생성 (폴더 안에 생성할 때)
npx create-next-app@14 . --typescript --tailwind --eslint --app --src-dir=no --import-alias="@/*"

# 프롬프트 응답 방법:
# ✔ Would you like to use TypeScript? → Yes
# ✔ Would you like to use ESLint? → Yes
# ✔ Would you like to use Tailwind CSS? → Yes
# ✔ Would you like to use `src/` directory? → No
# ✔ Would you like to use App Router? → Yes
# ✔ Would you like to customize the import alias? → No (그냥 Enter)

# Axios 설치
npm install axios

# 의존성 설치 완료 후
npm run dev

# 브라우저에서 확인
# http://localhost:3000
```

#### Step 9. 프론트엔드 환경변수 설정

`frontend/.env.local` 파일 생성:

```env
# 백엔드 API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

### 2.2 깃 협업 가이드

#### 팀장 기준 (최초 레포지토리 설정)

**Step 1. GitHub 레포지토리 생성**
1. [github.com](https://github.com) 로그인
2. `New repository` 클릭
3. Repository name: `kbo-predict`
4. Visibility: `Private`
5. **Add a README file**: 체크하지 않음
6. `Create repository` 클릭

**Step 2. 로컬 프로젝트와 연결**

```bash
# kbo-predict/ 루트에서 실행
cd kbo-predict

git init
git add .
git commit -m "chore: 프로젝트 초기 구조 세팅"

# GitHub 원격 저장소 연결 (YOUR_GITHUB_USERNAME 부분을 본인 아이디로 변경)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/kbo-predict.git

# main 브랜치로 첫 푸시
git branch -M main
git push -u origin main
```

**Step 3. .gitignore 설정**

`kbo-predict/.gitignore` 파일 생성:

```gitignore
# ── Python / Backend ──
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
venv/
.venv/
env/
*.egg-info/
dist/
build/

# 환경변수 (절대 커밋 금지!)
backend/.env
frontend/.env.local
.env
.env.*
!.env.example
!.env.local.example

# 모델 파일 (용량이 큼)
backend/app/ml/artifacts/*.pkl
backend/app/ml/artifacts/*.pt

# ── Node.js / Frontend ──
node_modules/
.next/
out/
frontend/.next/
npm-debug.log*

# ── IDE ──
.idea/
.vscode/
*.swp
*.swo

# ── OS ──
.DS_Store
Thumbs.db

# ── Docker ──
postgres_data/
redis_data/
```

**Step 4. 브랜치 보호 설정 (GitHub 웹에서)**
1. 레포지토리 → `Settings` → `Branches`
2. `Add branch protection rule`
3. Branch name pattern: `main`
4. `Require a pull request before merging` 체크
5. `Require approvals` → 1 선택
6. `Save changes`

---

#### 팀원 기준 (클론 이후 개발 시작)

**Step 1. 레포지토리 클론**

```bash
# 팀장이 공유한 레포 주소로 클론
git clone https://github.com/TEAM_GITHUB_USERNAME/kbo-predict.git
cd kbo-predict
```

**Step 2. 환경 설정**

```bash
# 백엔드 가상환경 및 패키지 설치
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env 파일 생성 (팀장에게 값 요청 후 작성)
cp .env.example .env
# .env 파일 열어서 팀장에게 받은 값 입력

# 프론트엔드 패키지 설치
cd ../frontend
npm install
cp .env.local.example .env.local
# .env.local 파일 열어서 값 입력
```

**Step 3. Docker 실행**

```bash
cd ..   # kbo-predict 루트로
docker compose up -d
```

**Step 4. 작업 브랜치 생성 후 개발**

```bash
# 항상 main을 최신으로 업데이트한 후 브랜치 생성
git checkout main
git pull origin main

# 브랜치 생성 (브랜치 전략 참고)
git checkout -b feat/backend-game-api

# 개발 후 커밋 & 푸시
git add .
git commit -m "feat(backend): 오늘의 경기 예측 API 구현"
git push origin feat/backend-game-api

# GitHub에서 PR(Pull Request) 생성
```

---

## 3. 개발

### 3.1.1 백엔드 (FastAPI)

#### 파일 구조 상세 설명

```
backend/
├── app/
│   ├── main.py               ← FastAPI 앱 생성, 라우터 등록, CORS 설정
│   ├── config.py             ← 환경변수 로드 (pydantic-settings)
│   │
│   ├── api/v1/
│   │   ├── router.py         ← v1 하위 모든 라우터 모음
│   │   ├── games.py          ← 경기 관련 엔드포인트
│   │   ├── teams.py          ← 팀 관련 엔드포인트
│   │   ├── pitchers.py       ← 투수 관련 엔드포인트
│   │   └── admin.py          ← 어드민 엔드포인트 (예측 수동 트리거)
│   │
│   ├── models/
│   │   ├── db/               ← SQLAlchemy ORM 모델 (DB 테이블 정의)
│   │   │   ├── base.py       ← DeclarativeBase 공통 클래스
│   │   │   ├── team.py
│   │   │   ├── player.py
│   │   │   ├── game.py
│   │   │   ├── prediction.py
│   │   │   ├── pitcher_stat.py
│   │   │   └── team_stat.py
│   │   └── schemas/          ← Pydantic 스키마 (요청/응답 형식 정의)
│   │       ├── game.py
│   │       ├── team.py
│   │       ├── pitcher.py
│   │       └── prediction.py
│   │
│   ├── services/             ← 비즈니스 로직 (핵심 로직은 여기)
│   │   ├── game_service.py   ← 오늘의 경기 조회, 캐싱 로직
│   │   ├── team_service.py   ← 팀 통계 집계
│   │   ├── pitcher_service.py ← 투수 통계 집계
│   │   └── ai_reasoning_service.py ← Claude API 근거 생성
│   │
│   ├── db/
│   │   ├── database.py       ← DB 연결, 세션 관리
│   │   └── redis_client.py   ← Redis 연결 및 캐싱 헬퍼
│   │
│   └── utils/
│       ├── logger.py         ← 로깅 설정
│       ├── cache.py          ← Redis 캐싱 데코레이터
│       └── exceptions.py     ← 커스텀 예외 클래스
│
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

#### 파일별 구현 가이드

##### `app/config.py` — 환경변수 설정

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Claude API
    claude_api_key: str = ""
    
    # ML 모델
    xgboost_artifact_path: str = "app/ml/artifacts/kbo_xgb_v1.pkl"
    lstm_artifact_path: str = "app/ml/artifacts/kbo_lstm_v1.pt"
    model_version: str = "v1.0-xgb+lstm"
    
    # 앱 설정
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    allowed_origins: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

##### `app/db/database.py` — DB 연결

```python
# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 연결 끊김 자동 감지
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI 의존성 주입용 DB 세션 생성기"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

##### `app/db/redis_client.py` — Redis 캐싱

```python
# backend/app/db/redis_client.py
import redis
import json
from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def get_cache(key: str):
    """캐시에서 값 조회. 없으면 None 반환."""
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def set_cache(key: str, data: dict, ttl_seconds: int = 1800):
    """캐시에 값 저장. ttl_seconds 초 후 자동 삭제."""
    redis_client.setex(key, ttl_seconds, json.dumps(data, ensure_ascii=False))

def delete_cache(key: str):
    """캐시 삭제 (예측 업데이트 후 호출)"""
    redis_client.delete(key)

def delete_cache_pattern(pattern: str):
    """패턴으로 캐시 일괄 삭제 (예: 'prediction:*')"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
```

##### `app/models/db/base.py` — ORM 베이스

```python
# backend/app/models/db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

##### `app/models/db/team.py` — 팀 ORM 모델

```python
# backend/app/models/db/team.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.db.base import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    short_name = Column(String(20), unique=True, nullable=False)
    logo_url = Column(String(255))
    home_stadium = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
```

##### `app/models/db/game.py` — 경기 ORM 모델

```python
# backend/app/models/db/game.py
from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.db.base import Base

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    stadium = Column(String(100))
    home_score = Column(SmallInteger)
    away_score = Column(SmallInteger)
    status = Column(String(20), default="SCHEDULED", nullable=False)
    # status: SCHEDULED | IN_PROGRESS | COMPLETED | CANCELLED | POSTPONED
    season = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 관계 (조인 시 자동으로 가져옴)
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    predictions = relationship("GamePrediction", back_populates="game")
    
    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="chk_different_teams"),
    )
```

##### `app/models/db/prediction.py` — 예측 ORM 모델

```python
# backend/app/models/db/prediction.py
from sqlalchemy import Column, Integer, Numeric, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.db.base import Base

class GamePrediction(Base):
    __tablename__ = "game_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    home_win_prob = Column(Numeric(5, 4), nullable=False)
    away_win_prob = Column(Numeric(5, 4), nullable=False)
    confidence_level = Column(String(10), default="MEDIUM", nullable=False)
    xgboost_home_prob = Column(Numeric(5, 4))
    pytorch_home_prob = Column(Numeric(5, 4))
    ensemble_weight_xgb = Column(Numeric(3, 2), default=0.60)
    ai_reasoning = Column(Text)
    home_starter_id = Column(Integer, ForeignKey("players.id"))
    away_starter_id = Column(Integer, ForeignKey("players.id"))
    is_final = Column(Boolean, default=False, nullable=False)
    model_version = Column(String(20))
    predicted_at = Column(DateTime, server_default=func.now(), nullable=False)
    actual_result = Column(String(10))
    
    game = relationship("Game", back_populates="predictions")
    home_starter = relationship("Player", foreign_keys=[home_starter_id])
    away_starter = relationship("Player", foreign_keys=[away_starter_id])
```

##### `app/models/schemas/game.py` — Pydantic 스키마

```python
# backend/app/models/schemas/game.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TeamBasic(BaseModel):
    id: int
    name: str
    short_name: str
    logo_url: Optional[str] = None

class StarterBasic(BaseModel):
    player_id: int
    name: str
    recent_era: Optional[float] = None

class PredictionCard(BaseModel):
    home_win_prob: float
    away_win_prob: float
    confidence_level: str
    home_starter: Optional[StarterBasic] = None
    away_starter: Optional[StarterBasic] = None
    updated_at: datetime

class GameCardResponse(BaseModel):
    game_id: int
    scheduled_at: datetime
    stadium: Optional[str] = None
    status: str
    home_team: TeamBasic
    away_team: TeamBasic
    prediction: Optional[PredictionCard] = None

class TodayGamesResponse(BaseModel):
    date: str
    games: list[GameCardResponse]
    total: int

    model_config = {"from_attributes": True}
```

##### `app/services/game_service.py` — 핵심 비즈니스 로직

```python
# backend/app/services/game_service.py
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.db.game import Game
from app.models.db.prediction import GamePrediction
from app.db.redis_client import get_cache, set_cache

CACHE_TTL_PREDICTIONS = 1800  # 30분

def get_today_games(db: Session, target_date: date = None) -> dict:
    """오늘의 경기 목록 반환. Redis 캐싱 적용."""
    
    if target_date is None:
        target_date = date.today()
    
    cache_key = f"predictions:today:{target_date.isoformat()}"
    
    # 1. Redis 캐시 우선 조회
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    # 2. DB 조회
    games = (
        db.query(Game)
        .options(
            joinedload(Game.home_team),
            joinedload(Game.away_team),
        )
        .filter(func.date(Game.scheduled_at) == target_date)
        .order_by(Game.scheduled_at)
        .all()
    )
    
    result_games = []
    for game in games:
        # 최신 확정 예측 조회
        prediction = (
            db.query(GamePrediction)
            .filter(
                GamePrediction.game_id == game.id,
                GamePrediction.is_final == True,
            )
            .order_by(GamePrediction.predicted_at.desc())
            .first()
        )
        
        game_data = _format_game_card(game, prediction, db)
        result_games.append(game_data)
    
    response = {
        "date": target_date.isoformat(),
        "games": result_games,
        "total": len(result_games),
    }
    
    # 3. Redis에 캐싱
    set_cache(cache_key, response, CACHE_TTL_PREDICTIONS)
    
    return response


def _format_game_card(game: Game, prediction: GamePrediction, db: Session) -> dict:
    """Game + Prediction 객체를 응답 딕셔너리로 변환"""
    from app.models.db.player import Player
    
    game_data = {
        "game_id": game.id,
        "scheduled_at": game.scheduled_at.isoformat(),
        "stadium": game.stadium,
        "status": game.status,
        "home_team": {
            "id": game.home_team.id,
            "name": game.home_team.name,
            "short_name": game.home_team.short_name,
            "logo_url": game.home_team.logo_url,
        },
        "away_team": {
            "id": game.away_team.id,
            "name": game.away_team.name,
            "short_name": game.away_team.short_name,
            "logo_url": game.away_team.logo_url,
        },
        "prediction": None,
    }
    
    if prediction:
        home_starter_data = None
        away_starter_data = None
        
        if prediction.home_starter_id:
            hs = db.query(Player).get(prediction.home_starter_id)
            if hs:
                home_starter_data = {"player_id": hs.id, "name": hs.name}
        
        if prediction.away_starter_id:
            as_ = db.query(Player).get(prediction.away_starter_id)
            if as_:
                away_starter_data = {"player_id": as_.id, "name": as_.name}
        
        game_data["prediction"] = {
            "home_win_prob": float(prediction.home_win_prob),
            "away_win_prob": float(prediction.away_win_prob),
            "confidence_level": prediction.confidence_level,
            "home_starter": home_starter_data,
            "away_starter": away_starter_data,
            "updated_at": prediction.predicted_at.isoformat(),
        }
    
    return game_data
```

##### `app/services/ai_reasoning_service.py` — Claude AI 근거 생성

```python
# backend/app/services/ai_reasoning_service.py
import anthropic
from app.config import settings

# Claude API 클라이언트 초기화
client = anthropic.Anthropic(api_key=settings.claude_api_key)

FALLBACK_REASONING = "현재 AI 근거를 생성할 수 없습니다. 통계 수치를 참고하여 예측 결과를 확인해주세요."

def generate_prediction_reasoning(
    home_team_name: str,
    away_team_name: str,
    home_win_prob: float,
    home_starter_name: str | None,
    away_starter_name: str | None,
    home_recent_stats: dict,
    away_recent_stats: dict,
) -> str:
    """Claude API를 사용하여 예측 근거 자연어 텍스트 생성"""
    
    if not settings.claude_api_key:
        return FALLBACK_REASONING
    
    prompt = f"""
KBO 야구 경기 예측 근거를 3~5문장으로 작성해주세요. 전문적이지만 야구를 모르는 사람도 이해할 수 있게 작성하세요.

경기 정보:
- 홈팀: {home_team_name} (승리 확률 {home_win_prob*100:.1f}%)
- 원정팀: {away_team_name} (승리 확률 {(1-home_win_prob)*100:.1f}%)
- 홈 선발 투수: {home_starter_name or '미확정'}
- 원정 선발 투수: {away_starter_name or '미확정'}
- 홈팀 최근 10경기: {home_recent_stats.get('wins', 'N/A')}승 {home_recent_stats.get('losses', 'N/A')}패
- 원정팀 최근 10경기: {away_recent_stats.get('wins', 'N/A')}승 {away_recent_stats.get('losses', 'N/A')}패

주의사항:
- 구체적인 수치와 이유를 포함하세요
- "예측합니다" 대신 현재형으로 작성하세요
- 3~5문장으로 제한하세요
"""
    
    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    
    except Exception as e:
        # Claude API 실패 시 Fallback
        print(f"Claude API 오류: {e}")
        return FALLBACK_REASONING
```

##### `app/api/v1/games.py` — 경기 API 라우터

```python
# backend/app/api/v1/games.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from app.db.database import get_db
from app.services.game_service import get_today_games, get_game_prediction_detail

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/today", summary="오늘의 경기 예측 목록")
def today_games(
    target_date: date = Query(default=None, description="조회 날짜 (YYYY-MM-DD). 기본값: 오늘"),
    db: Session = Depends(get_db),
):
    """
    당일 KBO 전 경기의 예측 카드 데이터를 반환합니다.
    Redis 캐시를 우선 조회하며, TTL은 30분입니다.
    """
    return get_today_games(db, target_date)


@router.get("/{game_id}/prediction", summary="경기 상세 예측")
def game_prediction(game_id: int, db: Session = Depends(get_db)):
    """
    특정 경기의 상세 예측 결과와 AI 생성 근거를 반환합니다.
    """
    result = get_game_prediction_detail(game_id, db)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={"code": "GAME_NOT_FOUND", "message": "해당 경기를 찾을 수 없습니다.", "status": 404}
        )
    return result
```

##### `app/api/v1/router.py` — 라우터 통합

```python
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import games, teams, pitchers, admin

api_router = APIRouter()

api_router.include_router(games.router)
api_router.include_router(teams.router)
api_router.include_router(pitchers.router)
api_router.include_router(admin.router)
```

##### `app/main.py` — FastAPI 앱 진입점

```python
# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.db.database import engine
from app.models.db.base import Base

# DB 테이블 자동 생성 (개발 환경)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KBO 야구 승부예측 AI API",
    description="XGBoost + LSTM 앙상블 모델로 KBO 경기를 예측하는 서비스",
    version="1.0.0",
    docs_url="/docs",         # Swagger UI 경로
    redoc_url="/redoc",       # ReDoc 경로
)

# CORS 설정 (프론트엔드 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# v1 라우터 등록
app.include_router(api_router, prefix=settings.api_v1_prefix)

# 루트 헬스체크
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "KBO Predict API", "version": "1.0.0"}

# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "서버 내부 오류가 발생했습니다.", "status": 500}}
    )
```

##### `app/scheduler/tasks.py` — 자동 스케줄링

```python
# backend/app/scheduler/tasks.py
# ⚠️ 이 파일은 AI&크롤링 파트(pipeline.py)와 연동됩니다.
# AI 파트의 run_daily_pipeline() 함수를 호출하는 스케줄러입니다.

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from app.db.database import SessionLocal

scheduler = BackgroundScheduler(timezone="Asia/Seoul")

def morning_task():
    """매일 06:00 — 전날 경기 결과 + 팀 순위 수집 (AI파트 pipeline 호출)"""
    logger.info("🌅 [스케줄러] 오전 수집 태스크 시작")
    db = SessionLocal()
    try:
        # AI 파트의 pipeline 임포트 (AI 파트 완성 후 활성화)
        # from app.crawler.pipeline import run_morning_pipeline
        # run_morning_pipeline(db)
        logger.info("✅ 오전 수집 완료")
    except Exception as e:
        logger.error(f"❌ 오전 수집 실패: {e}")
    finally:
        db.close()


def evening_task():
    """매일 18:00 — 선발 투수 + 날씨 수집"""
    logger.info("🌆 [스케줄러] 오후 수집 태스크 시작")
    # AI파트 evening pipeline 호출


def prediction_task():
    """매일 19:30 — ML 추론 + Claude AI 근거 생성"""
    logger.info("🤖 [스케줄러] 예측 태스크 시작")
    db = SessionLocal()
    try:
        from app.services.prediction_service import predict_all_today_games
        predict_all_today_games(db)
        logger.info("✅ 예측 완료")
    except Exception as e:
        logger.error(f"❌ 예측 실패: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(morning_task, CronTrigger(hour=6, minute=0), max_instances=1, id="morning")
    scheduler.add_job(evening_task, CronTrigger(hour=18, minute=0), max_instances=1, id="evening")
    scheduler.add_job(prediction_task, CronTrigger(hour=19, minute=30), max_instances=1, id="prediction")
    scheduler.start()
    logger.info("📅 APScheduler 시작 — 매일 06:00 / 18:00 / 19:30 자동 실행")


def stop_scheduler():
    scheduler.shutdown()
```

---

### 3.1.2 프론트엔드 (Next.js 14)

#### 파일 구조 상세 설명

```
frontend/
├── app/                       ← App Router 루트
│   ├── layout.tsx             ← 공통 레이아웃 (헤더 포함)
│   ├── page.tsx               ← 홈 화면 (HOME001 — 오늘의 경기 목록)
│   ├── loading.tsx            ← 전역 로딩 UI
│   ├── error.tsx              ← 전역 에러 UI
│   ├── not-found.tsx          ← 404 페이지
│   ├── games/
│   │   └── [id]/
│   │       └── page.tsx       ← 경기 상세 (GAME001)
│   └── stats/
│       └── page.tsx           ← 통계 페이지 (STAT001)
│
├── components/
│   ├── layout/
│   │   └── Header.tsx         ← 상단 네비게이션 바
│   ├── game/
│   │   ├── GameCard.tsx       ← 경기 예측 카드 (HOME002)
│   │   ├── ProbabilityBar.tsx ← 승리 확률 시각화 바
│   │   ├── ConfidenceBadge.tsx ← HIGH/MEDIUM/LOW 뱃지
│   │   └── AiReasoning.tsx    ← Claude AI 근거 텍스트 박스
│   ├── pitcher/
│   │   └── PitcherCard.tsx    ← 선발 투수 카드 (STAT003)
│   └── stats/
│       └── TeamStatTable.tsx  ← 팀 통계 테이블 (STAT002)
│
├── lib/
│   ├── api/
│   │   ├── client.ts          ← Axios 클라이언트 설정
│   │   ├── games.ts           ← 경기 관련 API 함수
│   │   ├── teams.ts           ← 팀 관련 API 함수
│   │   └── pitchers.ts        ← 투수 관련 API 함수
│   └── utils/
│       ├── date.ts            ← 날짜 포맷 유틸 (KST)
│       └── format.ts          ← 확률, 수치 포맷 유틸
│
└── types/
    └── index.ts               ← 공통 TypeScript 타입 정의
```

---

#### 파일별 구현 가이드

##### `types/index.ts` — 공통 타입 정의

```typescript
// frontend/types/index.ts

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
  pytorch_home_prob?: number;
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
    avg_ops: number;
    home_record: { wins: number; losses: number };
    away_record: { wins: number; losses: number };
    streak: string;
  };
  updated_at: string;
}
```

##### `lib/api/client.ts` — Axios 클라이언트

```typescript
// frontend/lib/api/client.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 10000, // 10초 타임아웃
  headers: {
    "Content-Type": "application/json",
  },
});

// 에러 인터셉터 (공통 에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 서버 응답 에러 (4xx, 5xx)
      console.error("API 에러:", error.response.data);
    } else if (error.request) {
      // 네트워크 에러 (서버 응답 없음)
      console.error("네트워크 오류 — 서버에 연결할 수 없습니다.");
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

##### `lib/api/games.ts` — 경기 API 함수

```typescript
// frontend/lib/api/games.ts
import apiClient from "./client";
import type { TodayGamesResponse, GameCard } from "@/types";

// 오늘의 경기 목록 조회
export async function fetchTodayGames(date?: string): Promise<TodayGamesResponse> {
  const params = date ? { date } : {};
  const { data } = await apiClient.get<TodayGamesResponse>("/games/today", { params });
  return data;
}

// 경기 상세 예측 조회
export async function fetchGamePrediction(gameId: number): Promise<GameCard> {
  const { data } = await apiClient.get<GameCard>(`/games/${gameId}/prediction`);
  return data;
}
```

##### `lib/utils/format.ts` — 포맷 유틸

```typescript
// frontend/lib/utils/format.ts

// 확률 % 변환 (0.62 → "62%")
export function formatProbability(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`;
}

// ERA 소수점 2자리
export function formatEra(era: number): string {
  return era.toFixed(2);
}

// 신뢰도 한글 변환
export function formatConfidence(level: "HIGH" | "MEDIUM" | "LOW"): string {
  const map = { HIGH: "높음", MEDIUM: "보통", LOW: "낮음" };
  return map[level];
}

// 신뢰도 색상 클래스 (Tailwind)
export function confidenceColor(level: "HIGH" | "MEDIUM" | "LOW"): string {
  const map = {
    HIGH: "bg-green-100 text-green-800",
    MEDIUM: "bg-yellow-100 text-yellow-800",
    LOW: "bg-gray-100 text-gray-600",
  };
  return map[level];
}
```

##### `components/game/ProbabilityBar.tsx` — 승리 확률 바

```tsx
// frontend/components/game/ProbabilityBar.tsx
import { formatProbability } from "@/lib/utils/format";

interface Props {
  homeTeamName: string;
  awayTeamName: string;
  homeWinProb: number;
  awayWinProb: number;
}

export default function ProbabilityBar({ homeTeamName, awayTeamName, homeWinProb, awayWinProb }: Props) {
  const homePercent = Math.round(homeWinProb * 100);
  const awayPercent = 100 - homePercent;

  return (
    <div className="w-full space-y-2">
      {/* 팀 이름 + 확률 */}
      <div className="flex justify-between text-sm font-semibold">
        <span className="text-blue-700">{homeTeamName} {formatProbability(homeWinProb)}</span>
        <span className="text-red-700">{awayTeamName} {formatProbability(awayWinProb)}</span>
      </div>

      {/* 확률 바 */}
      <div className="flex h-4 w-full rounded-full overflow-hidden">
        <div
          className="bg-blue-500 transition-all duration-500"
          style={{ width: `${homePercent}%` }}
        />
        <div
          className="bg-red-500 transition-all duration-500"
          style={{ width: `${awayPercent}%` }}
        />
      </div>
    </div>
  );
}
```

##### `components/game/ConfidenceBadge.tsx` — 신뢰도 뱃지

```tsx
// frontend/components/game/ConfidenceBadge.tsx
import { formatConfidence, confidenceColor } from "@/lib/utils/format";

interface Props {
  level: "HIGH" | "MEDIUM" | "LOW";
}

export default function ConfidenceBadge({ level }: Props) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor(level)}`}>
      신뢰도 {formatConfidence(level)}
    </span>
  );
}
```

##### `components/game/GameCard.tsx` — 경기 카드

```tsx
// frontend/components/game/GameCard.tsx
"use client";
import Link from "next/link";
import type { GameCard as GameCardType } from "@/types";
import ProbabilityBar from "./ProbabilityBar";
import ConfidenceBadge from "./ConfidenceBadge";

interface Props {
  game: GameCardType;
}

export default function GameCard({ game }: Props) {
  const { game_id, scheduled_at, stadium, home_team, away_team, prediction } = game;

  const gameTime = new Date(scheduled_at).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Link href={`/games/${game_id}`}>
      <div className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition-shadow cursor-pointer border border-gray-100">
        {/* 시간 + 구장 */}
        <div className="flex justify-between items-center mb-3 text-sm text-gray-500">
          <span>{gameTime}</span>
          <span>{stadium}</span>
        </div>

        {/* 팀 이름 */}
        <div className="flex justify-between items-center mb-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{home_team.short_name}</p>
            <p className="text-xs text-gray-400">홈</p>
          </div>
          <div className="text-gray-400 font-bold text-lg">VS</div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{away_team.short_name}</p>
            <p className="text-xs text-gray-400">원정</p>
          </div>
        </div>

        {/* 예측 정보 */}
        {prediction ? (
          <div className="space-y-3">
            <ProbabilityBar
              homeTeamName={home_team.short_name}
              awayTeamName={away_team.short_name}
              homeWinProb={prediction.home_win_prob}
              awayWinProb={prediction.away_win_prob}
            />
            <div className="flex justify-between items-center">
              <ConfidenceBadge level={prediction.confidence_level} />
              {prediction.home_starter && (
                <p className="text-xs text-gray-500">
                  선발: {prediction.home_starter.name} vs {prediction.away_starter?.name ?? "TBD"}
                </p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-400 text-sm py-2">예측 준비 중...</p>
        )}
      </div>
    </Link>
  );
}
```

##### `components/game/AiReasoning.tsx` — AI 근거 박스

```tsx
// frontend/components/game/AiReasoning.tsx
interface Props {
  reasoning: string;
}

export default function AiReasoning({ reasoning }: Props) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-blue-600 text-lg">🤖</span>
        <h3 className="font-semibold text-blue-800 text-sm">AI 예측 근거</h3>
      </div>
      <p className="text-gray-700 text-sm leading-relaxed">{reasoning}</p>
    </div>
  );
}
```

##### `app/page.tsx` — 홈 화면

```tsx
// frontend/app/page.tsx
import { fetchTodayGames } from "@/lib/api/games";
import GameCard from "@/components/game/GameCard";

export const revalidate = 1800; // 30분마다 정적 재생성

export default async function HomePage() {
  let data;
  try {
    data = await fetchTodayGames();
  } catch (e) {
    data = { date: "", games: [], total: 0 };
  }

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric", month: "long", day: "numeric", weekday: "long",
  });

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">오늘의 경기 예측</h1>
      <p className="text-gray-400 text-sm mb-6">{today}</p>

      {data.total === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">⚾</p>
          <p className="font-medium">오늘은 KBO 경기가 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.games.map((game) => (
            <GameCard key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </main>
  );
}
```

##### `app/games/[id]/page.tsx` — 경기 상세 페이지

```tsx
// frontend/app/games/[id]/page.tsx
import { fetchGamePrediction } from "@/lib/api/games";
import ProbabilityBar from "@/components/game/ProbabilityBar";
import ConfidenceBadge from "@/components/game/ConfidenceBadge";
import AiReasoning from "@/components/game/AiReasoning";
import { notFound } from "next/navigation";

interface Props {
  params: { id: string };
}

export default async function GameDetailPage({ params }: Props) {
  let game;
  try {
    game = await fetchGamePrediction(Number(params.id));
  } catch {
    notFound();
  }

  const { home_team, away_team, prediction, scheduled_at, stadium } = game;

  const gameTime = new Date(scheduled_at).toLocaleString("ko-KR");

  return (
    <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* 경기 헤더 */}
      <div className="bg-white rounded-xl shadow-md p-6 text-center">
        <p className="text-gray-400 text-sm mb-1">{gameTime} · {stadium}</p>
        <div className="flex justify-around items-center mt-3">
          <div>
            <p className="text-3xl font-bold">{home_team.short_name}</p>
            <p className="text-xs text-gray-400 mt-1">홈</p>
          </div>
          <span className="text-gray-300 font-bold text-xl">VS</span>
          <div>
            <p className="text-3xl font-bold">{away_team.short_name}</p>
            <p className="text-xs text-gray-400 mt-1">원정</p>
          </div>
        </div>
      </div>

      {/* 예측 상세 */}
      {prediction && (
        <>
          <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="font-bold text-gray-800">승리 확률</h2>
              <ConfidenceBadge level={prediction.confidence_level} />
            </div>
            <ProbabilityBar
              homeTeamName={home_team.short_name}
              awayTeamName={away_team.short_name}
              homeWinProb={prediction.home_win_prob}
              awayWinProb={prediction.away_win_prob}
            />
            {prediction.xgboost_home_prob && (
              <div className="text-xs text-gray-400 space-y-1">
                <p>XGBoost: {(prediction.xgboost_home_prob * 100).toFixed(1)}% / {((1 - prediction.xgboost_home_prob) * 100).toFixed(1)}%</p>
                {prediction.pytorch_home_prob && (
                  <p>LSTM: {(prediction.pytorch_home_prob * 100).toFixed(1)}% / {((1 - prediction.pytorch_home_prob) * 100).toFixed(1)}%</p>
                )}
              </div>
            )}
          </div>

          {/* AI 근거 */}
          {prediction.ai_reasoning && (
            <AiReasoning reasoning={prediction.ai_reasoning} />
          )}

          {/* 선발 투수 */}
          {(prediction.home_starter || prediction.away_starter) && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="font-bold text-gray-800 mb-3">선발 투수</h2>
              <div className="flex justify-around">
                <div className="text-center">
                  <p className="font-semibold">{prediction.home_starter?.name ?? "TBD"}</p>
                  {prediction.home_starter?.recent_era && (
                    <p className="text-sm text-gray-500">ERA {prediction.home_starter.recent_era.toFixed(2)}</p>
                  )}
                </div>
                <div className="text-center">
                  <p className="font-semibold">{prediction.away_starter?.name ?? "TBD"}</p>
                  {prediction.away_starter?.recent_era && (
                    <p className="text-sm text-gray-500">ERA {prediction.away_starter.recent_era.toFixed(2)}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  );
}
```

##### `components/layout/Header.tsx` — 헤더 네비게이션

```tsx
// frontend/components/layout/Header.tsx
import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <nav className="max-w-2xl mx-auto px-4 py-3 flex justify-between items-center">
        <Link href="/" className="font-bold text-lg text-blue-700">⚾ KBO 예측</Link>
        <div className="flex gap-4 text-sm font-medium text-gray-600">
          <Link href="/" className="hover:text-blue-700">오늘 경기</Link>
          <Link href="/stats" className="hover:text-blue-700">통계</Link>
        </div>
      </nav>
    </header>
  );
}
```

##### `app/layout.tsx` — 루트 레이아웃

```tsx
// frontend/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "KBO 야구 승부예측 AI",
  description: "XGBoost + LSTM 앙상블로 KBO 경기를 예측합니다",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <Header />
        {children}
      </body>
    </html>
  );
}
```

---

### 3.2 협업 가이드

#### 3.2.1 컨벤션 전략

##### 커밋 메시지 규칙

```
<타입>(<범위>): <내용>

예시:
feat(backend): 오늘의 경기 예측 API 구현
fix(frontend): GameCard 모바일 레이아웃 버그 수정
docs: API 명세 README 업데이트
chore: requirements.txt 패키지 버전 업데이트
refactor(backend): game_service 캐싱 로직 리팩토링
```

**타입 종류:**
- `feat`: 새 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정, 패키지 관리 등

##### Python 코드 스타일

```python
# ✅ 좋은 예
def get_today_games(db: Session, target_date: date = None) -> dict:
    """오늘의 경기 목록을 반환합니다. (docstring 필수)"""
    ...

# ❌ 나쁜 예
def get_games(db, dt=None):
    ...
```

- 함수명: `snake_case`
- 클래스명: `PascalCase`
- 타입 힌트 필수
- docstring 필수 (한 줄 이상)

##### TypeScript/React 스타일

```typescript
// ✅ 컴포넌트는 PascalCase
export default function GameCard({ game }: Props) { ... }

// ✅ 함수/변수는 camelCase
const fetchTodayGames = async () => { ... }

// ✅ 타입 정의는 types/index.ts에 집중
interface GameCard { ... }
```

##### 파일 구조 규칙

- 백엔드 API 엔드포인트: `api/v1/<리소스명>.py`
- 백엔드 비즈니스 로직: `services/<리소스명>_service.py`
- 프론트엔드 페이지: `app/<경로>/page.tsx`
- 프론트엔드 컴포넌트: `components/<카테고리>/<컴포넌트명>.tsx`

---

#### 3.2.2 브랜치 전략

**Git Flow 간소화 버전 (소규모 팀용)**

```
main          ← 배포 브랜치 (직접 push 금지, PR만 가능)
└── develop   ← 개발 통합 브랜치 (팀원들이 여기로 PR)
    ├── feat/backend-game-api       ← 기능 브랜치
    ├── feat/frontend-game-card
    ├── fix/prediction-cache-bug
    └── chore/docker-setup
```

**브랜치 명명 규칙:**

| 타입 | 형식 | 예시 |
|------|------|------|
| 기능 개발 | `feat/<담당>-<기능명>` | `feat/backend-game-api` |
| 버그 수정 | `fix/<이슈내용>` | `fix/today-games-null-error` |
| 문서 작업 | `docs/<내용>` | `docs/api-readme` |
| 환경 설정 | `chore/<내용>` | `chore/docker-compose` |

**작업 흐름:**

```bash
# 1. develop 최신화
git checkout develop && git pull origin develop

# 2. 브랜치 생성
git checkout -b feat/backend-teams-api

# 3. 개발 & 커밋
git add .
git commit -m "feat(backend): 팀 목록 API 구현"

# 4. 원격에 푸시
git push origin feat/backend-teams-api

# 5. GitHub에서 develop으로 PR 생성
# 6. 팀원 코드 리뷰 후 머지
# 7. 브랜치 삭제 (GitHub에서 자동 삭제 설정 권장)
```

---

## 4. 일정 및 계획표

### 2주 스프린트 (백엔드 + 프론트엔드 파트)

| 주차 | 일차 | 작업 내용 | 완료 기준 |
|------|------|-----------|-----------|
| **1주차** | Day 1 | 프로젝트 셋업, Docker 실행, DB 스키마 확인 | `docker compose ps` 모두 running |
| | Day 1 | `main.py`, `config.py`, `database.py` 구현 | `http://localhost:8000/docs` 접속 가능 |
| | Day 2 | ORM 모델 (`team.py`, `game.py`, `prediction.py`) 구현 | SQLAlchemy 모델 에러 없이 임포트 |
| | Day 2 | Pydantic 스키마 (`schemas/`) 구현 | 스키마 검증 테스트 통과 |
| | Day 3 | `GET /teams` API 완성 (DB 팀 목록 조회) | Swagger에서 10개 팀 응답 확인 |
| | Day 3 | `GET /games/today` API 완성 (빈 경기 목록) | 빈 배열 응답 정상 확인 |
| | Day 4 | Redis 캐싱 연동 (`redis_client.py`) | 캐시 저장/조회/삭제 동작 확인 |
| | Day 4 | `GET /teams/{id}/stats` API 완성 | 팀 통계 응답 정상 확인 |
| | Day 5 | `GET /pitchers/{id}/stats` API 완성 | 투수 통계 응답 정상 확인 |
| | Day 5 | APScheduler 설정 (스케줄 등록) | 서버 시작 시 스케줄러 로그 출력 |
| **2주차** | Day 6 | AI 파트와 `prediction_service.py` 인터페이스 연동 | `predict_game()` 함수 호출 성공 |
| | Day 6 | Claude API 근거 생성 연동 | AI 근거 텍스트 정상 생성 확인 |
| | Day 7 | Next.js 프론트엔드 초기화 및 `lib/api/` 구현 | `fetchTodayGames()` 응답 확인 |
| | Day 7 | `GameCard`, `ProbabilityBar`, `ConfidenceBadge` 컴포넌트 구현 | 홈 화면 경기 카드 렌더링 |
| | Day 8 | 홈 화면 (`app/page.tsx`) 완성 | 오늘의 경기 목록 실제 API 데이터로 표시 |
| | Day 9 | 경기 상세 페이지 (`app/games/[id]/page.tsx`) 완성 | GAME001, GAME002, GAME003 화면 완성 |
| | Day 10 | 통계 페이지 (`app/stats/page.tsx`) 완성 | STAT001, STAT002, STAT003 화면 완성 |
| | Day 11 | 전체 E2E 테스트 (홈→상세→통계 흐름) | 모든 화면 정상 동작 |
| | Day 12 | 버그 수정 및 UI 완성도 작업 | 디자인 QA 완료 |
| | Day 13 | 배포 (`Dockerfile` + EC2 설정) | 공개 URL 접속 가능 |
| | Day 14 | 최종 QA + README 작성 | 서비스 정상 운영 확인 |

---

## 5. 배포 가이드 (Docker + EC2)

### Step 1. 백엔드 Dockerfile 작성

`backend/Dockerfile`:

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 공개
EXPOSE 8000

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2. 프로덕션 docker-compose.yml

프로젝트 루트에 `docker-compose.prod.yml` 생성:

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  backend:
    build: ./backend
    container_name: kbo_backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://kbo_user:${DB_PASSWORD}@postgres:5432/kbo_predict
      - REDIS_URL=redis://redis:6379/0
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - APP_ENV=production
      - DEBUG=False
      - ALLOWED_ORIGINS=${FRONTEND_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:15-alpine
    container_name: kbo_postgres
    restart: always
    environment:
      POSTGRES_DB: kbo_predict
      POSTGRES_USER: kbo_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kbo_user -d kbo_predict"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: kbo_redis
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Step 3. AWS EC2 배포

```bash
# EC2 Ubuntu 인스턴스에 접속 후

# 1. Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# 2. Docker Compose 설치
sudo apt-get install docker-compose-plugin

# 3. 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/kbo-predict.git
cd kbo-predict

# 4. 프로덕션 환경변수 설정
cat > .env.prod << EOF
DB_PASSWORD=your_secure_password
CLAUDE_API_KEY=sk-ant-api03-xxxxx
FRONTEND_URL=https://your-frontend-domain.com
EOF

# 5. 프로덕션 서버 실행
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 6. 상태 확인
docker compose -f docker-compose.prod.yml ps
```

### Step 4. 프론트엔드 Vercel 배포 (권장)

```bash
# frontend/ 폴더에서

# Vercel CLI 설치
npm i -g vercel

# 배포
vercel

# 프롬프트:
# Set up and deploy? → Y
# Which scope? → 본인 계정 선택
# Link to existing project? → N (새 프로젝트)
# Project name? → kbo-predict-frontend
# Directory? → ./  (frontend 폴더에서 실행 중이므로)

# 환경변수 설정 (Vercel 대시보드에서)
# NEXT_PUBLIC_API_BASE_URL = https://your-ec2-ip:8000/api/v1
```

---

## 6. 최종 체크리스트

### 백엔드 체크리스트

- [ ] `docker compose up -d` 후 PostgreSQL + Redis 모두 running 상태
- [ ] `GET /teams` → 10개 팀 정상 응답
- [ ] `GET /games/today` → 경기 목록 (빈 배열 or 실제 데이터) 정상 응답
- [ ] `GET /games/{id}/prediction` → 예측 상세 + AI 근거 정상 응답
- [ ] `GET /teams/{id}/stats` → 팀 통계 정상 응답
- [ ] `GET /pitchers/{id}/stats` → 투수 통계 정상 응답
- [ ] Redis 캐싱 동작 확인 (두 번째 요청이 첫 번째보다 빠른지)
- [ ] APScheduler 3개 태스크 등록 확인 (서버 시작 로그)
- [ ] Claude API 연동 (근거 텍스트 생성 성공)
- [ ] Claude API 실패 시 Fallback 텍스트 동작 확인
- [ ] `.env` 파일이 Git에 올라가지 않았는지 확인
- [ ] `model_artifacts/` 파일이 `.gitignore`에 포함되었는지 확인

### 프론트엔드 체크리스트

- [ ] `npm run dev` 후 `http://localhost:3000` 접속 가능
- [ ] 홈 화면에 오늘의 경기 카드 목록 렌더링
- [ ] 경기 없는 날 안내 문구 표시
- [ ] 경기 카드 클릭 시 상세 페이지 이동
- [ ] 승리 확률 바 시각화 정상 표시
- [ ] 신뢰도 뱃지 (HIGH/MEDIUM/LOW) 색상 구분
- [ ] AI 예측 근거 텍스트 표시
- [ ] 선발 투수 정보 표시 (미확정 시 "TBD" 표시)
- [ ] 통계 페이지 팀 통계 테이블 렌더링
- [ ] 모바일 반응형 레이아웃 확인
- [ ] 404 에러 페이지 동작 확인
- [ ] `.env.local` 파일이 Git에 올라가지 않았는지 확인

### 배포 체크리스트

- [ ] EC2 인스턴스 보안 그룹에서 8000 포트 열기
- [ ] `docker compose -f docker-compose.prod.yml up -d` 성공
- [ ] 공개 IP로 API 접속 가능: `http://EC2_IP:8000/docs`
- [ ] Vercel 배포 성공 및 공개 URL 접속 가능
- [ ] 프론트엔드 → 백엔드 API 통신 확인 (CORS 에러 없음)
- [ ] 실제 경기 당일 19:30 이후 예측 데이터 정상 표시 확인

---

> 📌 **AI & 크롤링 파트 가이드라인은 별도 문서(`KBO_AI_크롤링_가이드라인.md`)를 참고하세요.**  
> 💬 **문의 또는 막히는 부분은 팀 슬랙/카톡에 즉시 공유하세요. 혼자 고민하지 마세요!**
