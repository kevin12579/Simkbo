# ⚾ SimKBO — KBO 야구 승부예측 AI

> XGBoost + LSTM 앙상블 모델로 KBO 경기 결과를 예측하고, Claude AI가 근거를 설명해주는 서비스

<br>

## 목차

- [프로젝트 소개](#프로젝트-소개)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [아키텍처](#아키텍처)
- [디렉토리 구조](#디렉토리-구조)
- [시작 가이드](#시작-가이드)
- [API 명세](#api-명세)
- [팀 소개](#팀-소개)

<br>

## 프로젝트 소개

SimKBO는 KBO 리그 10개 구단의 팀 순위, 선발 투수 통계, 최근 경기 흐름 등 수천 건의 데이터를 기반으로 당일 경기 승부를 예측하는 AI 서비스입니다.

- **데이터**: Statiz, KBO 공식 홈페이지, 네이버 스포츠에서 크롤링
- **예측**: XGBoost + LSTM 앙상블 (목표 정확도 60%+)
- **설명**: Claude AI가 각 경기별 예측 근거를 자연어로 생성

<br>

## 주요 기능

| 기능 | 설명 |
|------|------|
| 오늘의 경기 예측 | 당일 KBO 경기 홈팀 승률 시각화 |
| AI 예측 근거 | Claude API 기반 자연어 분석 리포트 |
| 팀 통계 조회 | 최근 10경기 성적, 홈/원정 분리 |
| 선발 투수 정보 | 최근 5선발 ERA·K/BB·WHIP |
| 자동 스케줄러 | 매일 06:00 데이터 수집 → 19:30 예측 갱신 |
| Redis 캐싱 | 반복 요청 응답 속도 최적화 |

<br>

## 기술 스택

**Backend**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat)

**ML / DL**

![XGBoost](https://img.shields.io/badge/XGBoost-2.0-FF6600?style=flat)
![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=flat&logo=scikitlearn&logoColor=white)

**Frontend**

![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)

**Infra / Tools**

![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.44-2EAD33?style=flat&logo=playwright&logoColor=white)

<br>

## 아키텍처

```
[ KBO 공식 / Statiz / 네이버 ] ──크롤링──▶ PostgreSQL
                                               │
                            build_training_data│
                                               ▼
                                   XGBoost + LSTM 앙상블
                                               │
                              predict_game()   │   APScheduler (19:30)
                                               ▼
                                        predictions 테이블
                                               │
                              FastAPI REST API │   Redis 캐시
                                               ▼
                                     Next.js 14 프론트엔드
```

**스케줄러 동작 흐름**

```
06:00  팀 순위 스냅샷 수집 (KBO 공식)
18:00  선발 투수 로스터 업데이트 (네이버)
19:30  오늘 경기 예측 실행 + Redis 캐시 무효화
```

<br>

## 디렉토리 구조

```
simkbo/
├── docker-compose.yml          # PostgreSQL 15 + Redis 7
├── db/
│   └── init.sql                # KBO 10개 구단 초기 데이터 포함 스키마
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 앱, lifespan, CORS
│   │   ├── config.py           # 환경변수 Settings
│   │   ├── api/v1/             # games / teams / pitchers / admin
│   │   ├── services/           # 비즈니스 로직 + Redis 캐싱
│   │   ├── models/
│   │   │   ├── db/             # SQLAlchemy ORM 모델
│   │   │   └── schemas/        # Pydantic 스키마
│   │   ├── crawler/            # KBO공식 / Statiz / 네이버 / 날씨
│   │   ├── ml/                 # 피처 엔지니어링, XGBoost, LSTM, 앙상블
│   │   ├── scheduler/          # APScheduler 태스크
│   │   ├── db/                 # database.py, redis_client.py
│   │   └── utils/              # logger, exceptions
│   ├── requirements.txt
│   ├── .env.example
│   └── seed_games.py           # 과거 경기 시드 스크립트
└── frontend/
    ├── app/
    │   ├── page.tsx            # 홈 (오늘의 경기 목록)
    │   ├── games/[id]/page.tsx # 경기 상세 + AI 근거
    │   └── stats/page.tsx      # 팀 통계 허브
    ├── components/
    │   ├── game/               # GameCard, ProbabilityBar, ConfidenceBadge, AiReasoning
    │   ├── layout/             # Header
    │   ├── pitcher/            # PitcherCard
    │   └── stats/              # TeamStatTable
    └── lib/
        ├── api/                # Axios 클라이언트 + 엔드포인트별 함수
        └── utils/              # 날짜·확률·ERA 포맷터
```

<br>

## 시작 가이드

### 요구사항

| 항목 | 버전 |
|------|------|
| Docker Desktop | 최신 |
| Python | 3.11 |
| Node.js | 18+ |

### 1. 저장소 클론 및 환경 설정

```bash
git clone https://github.com/kevin12579/simkbo.git
cd simkbo

# 백엔드 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env 열어서 아래 항목 입력:
#   STATIZ_USER, STATIZ_PASS   (Statiz 계정 — 크롤링 필수)
#   OPENAI_API_KEY             (예측 근거 생성 필수)
#   WEATHER_API_KEY            (날씨 피처 선택)

# 프론트엔드 환경변수 설정
cp frontend/.env.local.example frontend/.env.local
```

### 2. DB + Redis 시작

```bash
docker compose up -d
docker compose ps   # 모두 running 확인
```

### 3. 백엔드 서버 실행

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> 접속 확인: http://localhost:8000/docs

### 4. 프론트엔드 서버 실행 (새 터미널)

```bash
cd frontend
npm install
npm run dev
```

> 접속 확인: http://localhost:3000

### 5. 데이터 수집 (최초 1회)

> **순서를 반드시 지켜야 합니다.** 순서가 틀리면 FK 에러가 발생합니다.

```bash
cd backend
venv\Scripts\activate

# (1) Playwright 브라우저 설치
playwright install chromium

# (2) Statiz 최초 로그인 (브라우저 열림 → 수동 로그인 후 자동 저장)
python -m app.crawler.statiz_crawler

# (3) 과거 팀 순위 스냅샷 수집 (수 시간 소요, 1회만)
python -c "
from app.db.database import SessionLocal
from app.crawler.kbo_official_crawler import KBOOfficialCrawler
db = SessionLocal()
KBOOfficialCrawler().bulk_collect_snapshots('20230101', '20251231', db)
db.close()
"

# (4) 과거 경기 일정/결과 수집 (~10분)
python seed_games.py --seasons 2023 2024 2025

# (5) 선발 투수 시즌 통계 수집
python -c "
from app.db.database import SessionLocal
from app.crawler.statiz_crawler import StatizCrawler
db = SessionLocal()
c = StatizCrawler()
c.sync_all_pitchers(db, season=2024)
c.sync_all_pitchers(db, season=2025)
db.close()
"
```

수집 완료 확인:

```bash
docker exec kbo_postgres psql -U kbo_user -d kbo_predict -c "
SELECT 'snapshots' AS tbl, COUNT(*) FROM team_daily_snapshots
UNION ALL
SELECT 'games',            COUNT(*) FROM games
UNION ALL
SELECT 'pitcher_stats',   COUNT(*) FROM player_season_stats;
"
# 기대값: 7000+ / 2000+ / 수십+
```

### 6. 모델 학습

```bash
# XGBoost 학습 (필수)
python -m app.ml.build_training_data   # data/training_set.parquet 생성
python -m app.ml.xgboost_model         # artifacts/kbo_xgb_v1.pkl 생성

# LSTM 학습 (선택, GPU 권장)
python -c "
from app.db.database import SessionLocal
from app.ml.pytorch_model import train_pytorch_model
db = SessionLocal()
train_pytorch_model(db)
db.close()
"

# 백테스트 (목표: 60%+, 65% 초과 시 look-ahead bias 의심)
python -m app.ml.backtest
```

학습 완료 후 백엔드 서버를 재시작하면 모델이 자동 로드됩니다.

<br>

## API 명세

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/v1/games/today` | 오늘 경기 목록 + 예측 확률 |
| `GET` | `/api/v1/games/{id}/prediction` | 경기 상세 예측 + AI 근거 |
| `GET` | `/api/v1/teams` | 전체 팀 목록 |
| `GET` | `/api/v1/teams/{id}/stats` | 팀 통계 (최근 10경기, 홈/원정) |
| `GET` | `/api/v1/pitchers/{id}/stats` | 투수 통계 (최근 5선발) |
| `POST` | `/api/v1/admin/predictions/trigger` | 예측 수동 실행 |
| `POST` | `/api/v1/admin/cache/clear` | Redis 캐시 초기화 |

전체 스펙: http://localhost:8000/docs (Swagger UI)

<br>

## 팀 소개

| 팀 | 역할 |
|----|------|
| **A팀** | 데이터 수집 — Statiz, KBO 공식, 네이버 크롤러 개발 |
| **B팀** | ML/DL — 피처 엔지니어링, XGBoost, LSTM, 앙상블, 백테스트 |
| **C팀** | 서비스 — FastAPI 백엔드, Next.js 프론트엔드, Docker 인프라 |

<br>

## 알려진 주의사항

- **Docker 먼저 시작**: DB/Redis 없이 서버 시작하면 연결 오류 발생
- **Statiz 로그인은 1회만**: `playwright_profile/`에 세션 저장 → 이후 자동 재사용
- **games 시드는 모델 학습 전에 필수**: `games` 테이블이 비어 있으면 `build_training_data`가 0건으로 실패
- **`docker exec`에 `-it` 붙이지 말 것**: Windows PowerShell에서 "stdin is not a terminal" 오류 발생
- **모델 없이도 서버 실행 가능**: 예측 API 호출 시 `"XGBoost 모델이 로드되지 않았습니다"` 반환 (정상)
- **`seed_games.py` 재실행 안전**: 이미 있는 경기는 스코어만 업데이트 (중복 삽입 없음)
