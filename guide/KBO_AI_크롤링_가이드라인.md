# ⚾ KBO 야구 승부예측 AI — AI & 크롤링 개발 가이드라인 (A to Z)

> **대상 독자**: 데이터 수집(크롤링)과 ML/DL 모델 개발을 맡은 팀원. 처음 시작하는 사람도 따라할 수 있도록 작성되었습니다.  
> **담당 파트**: 데이터 크롤링 (A팀) + ML/DL 모델 개발 (B팀)  
> **MVP 범위**: P0 — XGBoost + LSTM 앙상블 예측 파이프라인, statiz/KBO/네이버 크롤러

---

## 목차

1. [프로젝트 요약](#1-프로젝트-요약)
   - 1.1 AI & 크롤링 파트 역할
   - 1.2 사용 기술 스택 및 설치 방법
   - 1.3 데이터 파이프라인 아키텍처
   - 1.4 데이터베이스 추가 테이블 설계
   - 1.5 백엔드 파트와의 인터페이스 명세
2. [세팅](#2-세팅)
   - 2.1 개발 환경 세팅 (Docker + Python)
   - 2.2 깃 협업 가이드
3. [개발](#3-개발)
   - 3.1 크롤링 파트 (A팀) 상세 가이드
   - 3.2 ML/DL 파트 (B팀) 상세 가이드
   - 3.3 협업 가이드
4. [일정 및 계획표](#4-일정-및-계획표)
5. [배포 가이드](#5-배포-가이드)
6. [최종 체크리스트](#6-최종-체크리스트)

---

## 1. 프로젝트 요약

### 1.1 AI & 크롤링 파트 역할

이 파트는 프로젝트의 **두뇌**입니다. 크게 두 가지 일을 합니다:

| 역할 | 담당 | 핵심 작업 |
|------|------|-----------|
| **A팀 — 데이터 수집** | 크롤링 담당 | statiz, KBO 공식, 네이버스포츠, 기상청에서 경기/선수/팀 데이터 수집 → PostgreSQL 저장 |
| **B팀 — ML/DL 모델** | 모델 개발 담당 | 수집된 데이터로 피처 엔지니어링 → XGBoost 학습 → LSTM 학습 → 앙상블 → 예측 서빙 |

**전체 흐름:**
```
[외부 사이트] → [A팀 크롤러] → [PostgreSQL DB] → [B팀 피처 엔지니어링]
                                                          ↓
                                              [XGBoost + LSTM 앙상블]
                                                          ↓
                                              [Claude API 근거 생성]
                                                          ↓
                                              [백엔드 API → 프론트엔드]
```

---

### 1.2 사용 기술 스택 및 설치 방법

#### AI & 크롤링 전용 기술 스택

| 영역 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **크롤링** | requests | 2.32.x | HTTP 요청 |
| | BeautifulSoup4 | 4.12.x | HTML 파싱 |
| | Playwright | 1.44.x | SPA 동적 페이지 크롤링 (네이버 등) |
| | lxml | 5.x | 빠른 XML/HTML 파서 |
| **데이터 처리** | pandas | 2.2.x | 데이터 전처리, 피처 엔지니어링 |
| | numpy | 1.26.x | 수치 연산 |
| | pyarrow | 16.x | Parquet 파일 저장 |
| **ML — Stage 1** | xgboost | 2.0.x | XGBoost 분류 모델 |
| | scikit-learn | 1.4.x | 평가지표, calibration |
| | optuna | 3.6.x | 하이퍼파라미터 튜닝 |
| | joblib | 1.4.x | 모델 직렬화 저장 |
| **ML — Stage 2** | torch | 2.3.x | PyTorch LSTM 모델 |
| | tqdm | 4.66.x | 진행률 표시 |
| **분석/시각화** | matplotlib | 3.9.x | 모델 평가 시각화 |
| | jupyter | 1.x | 탐색적 데이터 분석 노트북 |

#### 추가 패키지 설치

`backend/requirements.txt`에 아래 내용을 **추가**하세요 (백엔드 파트의 requirements.txt와 통합):

```txt
# ── 크롤링 ──
beautifulsoup4==4.12.3
lxml==5.2.2
playwright==1.44.0

# ── 데이터 처리 ──
pandas==2.2.2
numpy==1.26.4
pyarrow==16.1.0

# ── ML ──
xgboost==2.0.3
scikit-learn==1.4.2
optuna==3.6.1
joblib==1.4.2

# ── DL ──
torch==2.3.1
tqdm==4.66.4

# ── 시각화 ──
matplotlib==3.9.0
jupyter==1.0.0
```

```bash
# 설치 (backend/ 폴더에서 venv 활성화 후)
pip install -r requirements.txt

# Playwright 브라우저 설치 (크롤링용)
playwright install chromium
```

---

### 1.3 데이터 파이프라인 아키텍처

#### 크롤링 스케줄 (APScheduler)

| 시각 | 태스크 | 수집 내용 | 소요 시간 |
|------|--------|-----------|-----------|
| 매일 **06:00** | 오전 수집 | 전날 경기 결과, 팀 순위(KBO 공식), 선수 시즌 통계(statiz) | ~20분 |
| 매일 **18:00** | 오후 수집 | 당일 선발 투수 확정(네이버), 날씨(기상청) | ~5분 |
| 매일 **19:30** | ML 추론 | XGBoost + LSTM 앙상블 실행, Claude API 근거 생성, DB 저장 | ~5분 |

#### 크롤러별 데이터 소스

| 크롤러 | 사이트 | 데이터 | 인증 필요 |
|--------|--------|--------|-----------|
| `statiz_crawler.py` | statiz.co.kr | 선수 시즌 통계(ERA, WHIP, OPS 등), 경기별 기록 | **로그인 필요** |
| `kbo_official_crawler.py` | koreabaseball.com | 팀 순위, 최근 10경기, 연승/연패, 일정 | 없음 |
| `naver_crawler.py` | sports.naver.com | 당일 선발 투수, 라인업, 경기 결과 | 없음 |
| `weather_client.py` | 기상청 API | 경기 당일 날씨(강수확률, 풍속) | API 키 필요 |

#### ML 파이프라인 흐름

```
[PostgreSQL]
     │
     ▼
[feature_engineering.py]  ← as_of_date 기준 피처 생성 (47개)
     │
     ├── [xgboost_model.py]  Stage 1 — 정형 데이터 분류
     │         │
     │         └── xgboost_home_prob (예: 0.61)
     │
     ├── [pytorch_model.py]  Stage 2 — 시계열 LSTM
     │         │
     │         └── lstm_home_prob (예: 0.64)
     │
     ▼
[ensemble.py]  신뢰도 기반 동적 가중 앙상블
     │
     └── home_win_prob / away_win_prob / confidence_level
              │
              ▼
     [prediction_service.py]  ← 백엔드 파트에서 호출
              │
              ▼
     [PostgreSQL: game_predictions]
              │
              ▼
           [Redis 캐시]
```

---

### 1.4 데이터베이스 추가 테이블 설계

> **백엔드 파트의 `db/init.sql`에는 기본 테이블이 있습니다.**  
> **아래 테이블들은 AI 파트에서 추가로 필요한 테이블입니다. A팀이 마이그레이션을 적용합니다.**

`db/init.sql` 끝에 아래 SQL을 추가하거나, 별도 마이그레이션 파일로 관리하세요.

```sql
-- ============================================================
-- AI & 크롤링 파트 추가 테이블
-- ============================================================

-- team_daily_snapshots (일별 팀 순위 스냅샷 — 시점 백테스트의 핵심)
-- "2024년 5월 1일 경기"를 예측할 때 그 시점에 알 수 있는 팀 정보만 사용
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

-- player_season_stats (선수 시즌 누적 통계)
-- 매 경기마다 집계 쿼리를 돌리는 대신, 시즌 통계를 미리 저장
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
  -- 메타
  updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(player_id, season)
);

-- team_season_stats (팀 시즌 합산 통계)
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
```

---

### 1.5 백엔드 파트와의 인터페이스 명세

> **B팀이 완성하면 백엔드 파트에 전달해야 하는 함수 시그니처입니다.**  
> 이 인터페이스를 지키면 백엔드 파트가 바로 호출할 수 있습니다.

#### `prediction_service.py` 핵심 함수

```python
# backend/app/services/prediction_service.py
# B팀이 구현, 백엔드 파트(C팀)에서 호출

def predict_game(game_id: int, db: Session) -> dict:
    """
    단일 경기 예측 실행. 백엔드 스케줄러에서 호출됩니다.
    
    Returns:
        {
            "home_win_prob": 0.62,      # 홈팀 승리 확률
            "away_win_prob": 0.38,
            "confidence_level": "HIGH",  # HIGH | MEDIUM | LOW
            "xgboost_home_prob": 0.61,
            "lstm_home_prob": 0.64,
            "model_version": "v1.0-xgb+lstm",
            "features_used": 47,
            "predicted_at": "2025-05-12T19:30:00+09:00"
        }
    """
    ...

def predict_all_today_games(db: Session) -> list[dict]:
    """
    오늘 모든 경기 예측. 스케줄러 19:30 태스크에서 호출됩니다.
    각 경기의 예측 결과를 game_predictions 테이블에 저장합니다.
    """
    ...
```

#### 피처 공유 스펙 (A↔B 합의)

```python
# 피처 컬럼명 순서 고정 — A팀이 생성, B팀이 학습에 사용
FEATURE_COLUMNS = [
    # 그룹 1: 팀 누적 통계
    "home_season_win_rate", "away_season_win_rate",
    "home_last10_win_rate", "away_last10_win_rate",
    "home_home_win_rate", "away_away_win_rate",
    "home_streak", "away_streak",
    # 그룹 2: 팀 타격/투구
    "home_ops", "away_ops",
    "home_era", "away_era",
    "home_run_diff_last10", "away_run_diff_last10",
    # 그룹 3: 선발 투수
    "home_starter_era", "away_starter_era",
    "home_starter_recent5_era", "away_starter_recent5_era",
    "home_starter_whip", "away_starter_whip",
    # 그룹 4: 불펜 & 타선
    "home_bullpen_era", "away_bullpen_era",
    "home_top5_ops", "away_top5_ops",
    "home_hr_power", "away_hr_power",
    # 그룹 5: H2H & 컨텍스트
    "h2h_home_win_rate",
    "rest_diff", "is_weekend", "is_dome",
    # 그룹 6: 차이값 피처 (diff)
    "era_diff", "ops_diff", "last10_wr_diff",
    "season_wr_diff", "starter_era_diff",
    "bullpen_era_diff", "top5_ops_diff",
    "streak_diff", "home_win_rate_diff",
    "run_diff_diff", "hr_power_diff",
    "pitcher_whip_diff", "pitcher_recent5_era_diff",
    "h2h_diff",
]
# 총 47개 (인덱스 0~46), 순서 변경 금지
```

---

## 2. 세팅

### 2.1 개발 환경 세팅

> **백엔드 파트의 Docker (PostgreSQL + Redis) 세팅이 완료되어 있어야 합니다.**  
> 백엔드 파트 가이드라인의 `2.1 세팅` 섹션을 먼저 완료하세요.

#### Step 1. 디렉토리 구조 추가 생성

```bash
# kbo-predict/ 루트에서 실행
cd backend

# AI 파트 전용 디렉토리 추가
mkdir -p app/ml/artifacts
mkdir -p app/crawler
mkdir -p data/cache
mkdir -p notebooks

echo "✅ AI 파트 폴더 생성 완료"
```

#### Step 2. 파이썬 가상환경 활성화 및 AI 패키지 설치

```bash
cd backend
source venv/bin/activate   # (venv) 표시 확인

# AI/ML 추가 패키지 설치 (requirements.txt에 추가 후)
pip install beautifulsoup4 lxml playwright pandas numpy pyarrow
pip install xgboost scikit-learn optuna joblib
pip install torch tqdm matplotlib jupyter

# Playwright 브라우저 설치
playwright install chromium

# 설치 확인
python -c "import xgboost; print('XGBoost:', xgboost.__version__)"
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
```

#### Step 3. .env 파일에 AI 파트 전용 환경변수 추가

`backend/.env`에 아래 내용을 추가:

```env
# ── Statiz 크롤링 계정 (반드시 본인 계정 사용) ──
STATIZ_USER=your_statiz_email@example.com
STATIZ_PASS=your_statiz_password

# ── 기상청 API ──
# https://www.data.go.kr 에서 신청
WEATHER_API_KEY=your_weather_api_key

# ── 모델 설정 ──
XGBOOST_ARTIFACT_PATH=app/ml/artifacts/kbo_xgb_v1.pkl
LSTM_ARTIFACT_PATH=app/ml/artifacts/kbo_lstm_v1.pt
CALIBRATOR_PATH=app/ml/artifacts/calibrator.pkl
MODEL_VERSION=v1.0-xgb+lstm
```

> **❗ 주의**: Statiz 계정은 개인 계정을 사용하세요. 크롤링 빈도를 낮추고 (요청 간 2초 간격), 서비스 이용약관을 준수하세요.

#### Step 4. 추가 DB 테이블 적용

```bash
# Docker가 실행 중인지 확인
docker compose ps

# 추가 테이블 SQL 적용
docker exec -i kbo_postgres psql -U kbo_user -d kbo_predict << 'EOF'
-- team_daily_snapshots, player_season_stats, team_season_stats 생성
-- (1.4절의 SQL 내용 붙여넣기)
EOF

# 테이블 생성 확인
docker exec -it kbo_postgres psql -U kbo_user -d kbo_predict \
  -c "\dt" | grep -E "team_daily|player_season|team_season"
```

---

### 2.2 깃 협업 가이드

> **기본 깃 설정은 백엔드 파트 가이드라인의 `2.2절`을 참고하세요.**

#### A팀 (크롤링) 브랜치 전략

```bash
# 기능별 브랜치 생성
git checkout develop
git pull origin develop

# 크롤러 개발
git checkout -b feat/crawler-kbo-official      # KBO 공식 크롤러
git checkout -b feat/crawler-statiz             # Statiz 크롤러
git checkout -b feat/crawler-naver              # 네이버 크롤러
git checkout -b feat/crawler-pipeline           # 통합 파이프라인
```

#### B팀 (ML/DL) 브랜치 전략

```bash
# ML 개발 브랜치
git checkout -b feat/ml-feature-engineering    # 피처 엔지니어링
git checkout -b feat/ml-xgboost               # XGBoost 모델
git checkout -b feat/ml-pytorch-lstm          # PyTorch LSTM
git checkout -b feat/ml-ensemble              # 앙상블 로직
```

#### `data/` 폴더 .gitignore 추가

`backend/.gitignore` (또는 루트 `.gitignore`)에 추가:

```gitignore
# ── AI 파트 데이터 & 모델 파일 ──
data/
!data/.gitkeep         # 빈 data/ 폴더는 유지
notebooks/.ipynb_checkpoints/
*.pkl                  # 모델 파일 (용량 큼)
*.pt                   # PyTorch 모델 파일
app/ml/artifacts/      # 아티팩트 폴더 전체 무시
```

```bash
# 빈 폴더 유지를 위한 .gitkeep 파일 생성
touch data/.gitkeep
touch app/ml/artifacts/.gitkeep
```

---

## 3. 개발

### 3.1 크롤링 파트 (A팀) 상세 가이드

#### 파일 구조 설명

```
backend/app/crawler/
├── __init__.py
├── base_crawler.py         ← 공통 베이스: 세션, 재시도, 딜레이, UA 로테이션
├── statiz_crawler.py       ← Statiz 선수 시즌 통계 (로그인 필요)
├── kbo_official_crawler.py ← KBO 공식 팀 순위/일정 (로그인 불필요)
├── naver_crawler.py        ← 네이버스포츠 선발 투수, 경기 결과
├── weather_client.py       ← 기상청 Open API 날씨
├── roster.py               ← KBO 10개 팀 로스터 정의 (수동 유지)
└── pipeline.py             ← 통합 실행기 (스케줄러에서 호출)
```

---

#### 파일별 구현 가이드

##### `app/crawler/base_crawler.py` — 모든 크롤러의 기반

```python
# backend/app/crawler/base_crawler.py
"""
모든 크롤러가 상속하는 베이스 클래스.
핵심 기능:
  - 요청 간 2초 딜레이 + 무작위 지터 (봇 탐지 회피)
  - 403/429 에러 시 지수 백오프 재시도
  - User-Agent 로테이션
  - 모든 크롤링 결과를 crawl_logs 테이블에 기록
"""
import time
import random
import logging
from typing import Optional

import requests
from sqlalchemy.orm import Session
from app.models.db.crawl_log import CrawlLog

logger = logging.getLogger(__name__)

# 3~5개 User-Agent 로테이션 (봇 탐지 우회)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class BaseCrawler:
    """
    사용 방법:
        class MyCrawler(BaseCrawler):
            def crawl(self):
                resp = self.safe_get("https://example.com")
                soup = BeautifulSoup(resp.text, "html.parser")
                ...
    """
    
    def __init__(
        self,
        delay: float = 2.0,      # 요청 간 기본 딜레이 (초)
        max_retries: int = 3,     # 최대 재시도 횟수
        retry_wait: int = 30,     # 첫 재시도 대기 시간 (초)
    ):
        self.delay = delay
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.session = requests.Session()
        self._rotate_ua()

    def _rotate_ua(self):
        """User-Agent를 무작위로 변경합니다."""
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def safe_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        안전한 HTTP GET 요청.
        - 200 성공: 응답 반환 후 딜레이 적용
        - 403/429: 백오프 후 UA 로테이션 재시도
        - 기타 에러: 예외 발생
        """
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=15, **kwargs)
                resp.encoding = "utf-8"
                
                if resp.status_code == 200:
                    # 딜레이 + 지터 (0~0.5초 무작위 추가)
                    time.sleep(self.delay + random.uniform(0, 0.5))
                    return resp
                
                if resp.status_code in (403, 429):
                    wait_time = self.retry_wait * (attempt + 1)
                    logger.warning(
                        f"[{resp.status_code}] {url} — {wait_time}초 대기 후 재시도 "
                        f"({attempt + 1}/{self.max_retries})"
                    )
                    self._rotate_ua()
                    time.sleep(wait_time)
                    continue
                
                resp.raise_for_status()
                
            except requests.RequestException as e:
                logger.error(f"요청 실패: {url} — {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_wait)
                    continue
        
        logger.error(f"최대 재시도 초과: {url}")
        return None

    def log_crawl_result(
        self,
        db: Session,
        source: str,
        task_type: str,
        status: str,
        records: int = 0,
        error: str = None,
    ):
        """크롤링 결과를 crawl_logs 테이블에 기록합니다."""
        log = CrawlLog(
            source=source,
            task_type=task_type,
            status=status,
            records_collected=records,
            error_message=error,
        )
        db.add(log)
        db.commit()
```

##### `app/crawler/roster.py` — 팀 로스터 정의

```python
# backend/app/crawler/roster.py
"""
KBO 10개 팀의 주요 선발 투수 로스터.
시즌이 바뀌면 이 파일을 수동 업데이트하세요.
외국인 선수는 is_foreign=True 표시.
"""

# 팀 short_name → 선수 목록 매핑
ROSTERS = {
    "두산": [
        {"name": "곽빈",   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "이영하", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "알칸타라", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
    "LG": [
        {"name": "임찬규", "position": "PITCHER", "throw_hand": "LEFT", "is_foreign": False},
        {"name": "엔스",   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
    "키움": [
        {"name": "하영민", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "KT": [
        {"name": "벤자민", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "고영표", "position": "PITCHER", "throw_hand": "LEFT", "is_foreign": False},
    ],
    "SSG": [
        {"name": "로무알도", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "김광현",   "position": "PITCHER", "throw_hand": "LEFT", "is_foreign": False},
    ],
    "NC": [
        {"name": "레예스", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "류진욱", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "KIA": [
        {"name": "양현종",   "position": "PITCHER", "throw_hand": "LEFT", "is_foreign": False},
        {"name": "네일",     "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
    "롯데": [
        {"name": "반즈",   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "박세웅", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "삼성": [
        {"name": "원태인", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "뷰캐넌", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
    "한화": [
        {"name": "류현진",  "position": "PITCHER", "throw_hand": "LEFT", "is_foreign": False},
        {"name": "라이온스", "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
}

def get_all_pitchers() -> list[dict]:
    """모든 팀의 투수 목록 반환"""
    result = []
    for team_name, players in ROSTERS.items():
        for p in players:
            result.append({**p, "team_short_name": team_name})
    return result
```

##### `app/crawler/kbo_official_crawler.py` — KBO 공식 팀 순위

```python
# backend/app/crawler/kbo_official_crawler.py
"""
KBO 공식 사이트에서 팀 순위 스냅샷 수집.

핵심 기능:
  - fetch_team_rank_daily(date): 특정 날짜의 팀 순위 스냅샷 (시점 백테스트 핵심)
  - fetch_schedule(year, month): 월별 경기 일정

왜 이 크롤러가 중요한가:
  - 과거 임의 날짜의 팀 순위를 조회할 수 있어 look-ahead bias 없는 학습 데이터 생성 가능
  - 예: 2024-05-01 경기 학습 시, 그 날 기준 순위만 사용 (5월~10월 누적값 X)
"""
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawler.base_crawler import BaseCrawler
from app.models.db.team_snapshot import TeamDailySnapshot
from app.models.db.team import Team


class KBOOfficialCrawler(BaseCrawler):
    BASE_URL = "https://www.koreabaseball.com"
    
    def fetch_team_rank_daily(self, date_str: str) -> list[dict]:
        """
        date_str: 'YYYYMMDD' 형식 (예: '20240501')
        특정 날짜의 팀 순위 스냅샷을 반환합니다.
        """
        url = f"{self.BASE_URL}/Record/TeamRank/TeamRankDaily.aspx?seriesId=0&date={date_str}"
        resp = self.safe_get(url)
        if not resp:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 순위 테이블 파싱
        # 실제 HTML 구조는 사이트에서 직접 확인 필요 (F12 → 개발자 도구)
        table = soup.select_one("table.tData")
        if not table:
            return []
        
        rows = []
        for tr in table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if len(cells) < 10:
                continue
            
            # 컬럼 순서: 순위 | 팀 | 경기수 | 승 | 패 | 무 | 승률 | 게임차 | 최근10경기 | 연속
            try:
                last10 = cells[8]  # 예: "7승 3패"
                last10_wins = int(last10.split("승")[0]) if "승" in last10 else 0
                last10_losses = int(last10.split("승")[1].replace("패", "").strip()) if "패" in last10 else 0
                
                streak = cells[9]  # 예: "3연승" or "2연패"
                streak_type = "WIN" if "연승" in streak else "LOSS" if "연패" in streak else "DRAW"
                streak_count = int("".join(filter(str.isdigit, streak))) if streak else 0
                
                rows.append({
                    "rank": int(cells[0]),
                    "team_name": cells[1],          # "두산" 또는 "LG" 등
                    "games_played": int(cells[2]),
                    "wins": int(cells[3]),
                    "losses": int(cells[4]),
                    "draws": int(cells[5]),
                    "season_win_rate": float(cells[6]),
                    "last10_wins": last10_wins,
                    "last10_losses": last10_losses,
                    "streak_type": streak_type,
                    "streak_count": streak_count,
                })
            except (ValueError, IndexError) as e:
                continue
        
        return rows
    
    def save_team_snapshots(
        self,
        date_str: str,
        db: Session,
    ) -> int:
        """
        특정 날짜의 팀 순위를 team_daily_snapshots 테이블에 저장.
        이미 있으면 덮어씁니다 (UPSERT).
        """
        from datetime import datetime
        snapshot_date = datetime.strptime(date_str, "%Y%m%d").date()
        
        rows = self.fetch_team_rank_daily(date_str)
        if not rows:
            return 0
        
        # 팀 이름 → DB ID 매핑
        teams = {t.short_name: t.id for t in db.query(Team).all()}
        
        saved_count = 0
        for row in rows:
            team_id = teams.get(row["team_name"])
            if not team_id:
                continue
            
            # UPSERT: 이미 있으면 업데이트
            existing = db.query(TeamDailySnapshot).filter_by(
                team_id=team_id, snapshot_date=snapshot_date
            ).first()
            
            if existing:
                for key, value in row.items():
                    if key != "team_name":
                        setattr(existing, key, value)
            else:
                snapshot = TeamDailySnapshot(
                    team_id=team_id,
                    snapshot_date=snapshot_date,
                    **{k: v for k, v in row.items() if k != "team_name"}
                )
                db.add(snapshot)
            
            saved_count += 1
        
        db.commit()
        return saved_count
    
    def bulk_collect_snapshots(
        self,
        start_date: str,
        end_date: str,
        db: Session,
    ) -> dict:
        """
        날짜 범위의 모든 팀 순위 스냅샷 수집.
        학습 데이터 구축 시 1회 실행 (3시즌 = 약 1,000일 × 10팀 = 10,000행).
        
        start_date, end_date: 'YYYYMMDD' 형식
        """
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        
        total_saved = 0
        current = start
        
        while current <= end:
            date_str = current.strftime("%Y%m%d")
            try:
                count = self.save_team_snapshots(date_str, db)
                total_saved += count
                print(f"✅ {date_str}: {count}개 저장")
            except Exception as e:
                print(f"❌ {date_str}: 실패 — {e}")
            
            current += timedelta(days=1)
        
        return {"total_saved": total_saved}
```

##### `app/crawler/statiz_crawler.py` — Statiz 선수 통계

```python
# backend/app/crawler/statiz_crawler.py
"""
statiz.co.kr에서 선수 시즌 통계 수집.

로그인 방식: requests Session으로 로그인 후 쿠키 유지
수집 데이터:
  - 투수 시즌 통계: ERA, WHIP, FIP, 이닝, 삼진, 볼넷, WAR
  - 타자 시즌 통계: AVG, OBP, SLG, OPS, HR, RBI, WAR

주의사항:
  - 요청 간 반드시 2초 이상 딜레이
  - player_ids.json 캐시로 중복 검색 방지
  - is_foreign 필드는 roster.py 기준으로 설정
"""
import json
import os
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawler.base_crawler import BaseCrawler
from app.config import settings

CACHE_FILE = Path("data/cache/player_ids.json")
STATIZ_BASE = "https://statiz.sporki.com"


class StatizCrawler(BaseCrawler):
    
    def __init__(self):
        super().__init__(delay=2.5)  # Statiz는 딜레이를 더 길게
        self._player_id_cache: dict = {}
        self._logged_in = False
        self._load_cache()

    def _load_cache(self):
        """player_ids.json 캐시 로드 (있으면)"""
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                self._player_id_cache = json.load(f)
            print(f"캐시 로드: {len(self._player_id_cache)}명")

    def _save_cache(self):
        """player_ids.json 캐시 저장"""
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._player_id_cache, f, ensure_ascii=False, indent=2)

    def login(self) -> bool:
        """Statiz 로그인. 성공 시 True 반환."""
        login_url = f"{STATIZ_BASE}/account/login"
        
        # 로그인 페이지에서 CSRF 토큰 가져오기 (필요한 경우)
        login_page = self.safe_get(login_url)
        if not login_page:
            return False
        
        # 로그인 POST 요청
        resp = self.session.post(login_url, data={
            "user_id": settings.statiz_user,
            "user_pw": settings.statiz_pass,
        }, allow_redirects=True)
        
        # 로그인 성공 여부 확인 (로그인 후 리다이렉트 URL 확인)
        self._logged_in = resp.url != login_url
        if self._logged_in:
            print("✅ Statiz 로그인 성공")
        else:
            print("❌ Statiz 로그인 실패 — 계정 정보를 확인하세요")
        
        return self._logged_in

    def search_player(self, name: str) -> Optional[str]:
        """
        선수 이름으로 Statiz player_no 검색.
        캐시에 있으면 캐시 반환.
        
        Returns: player_no (예: "p10001") or None
        """
        # 캐시 확인
        if name in self._player_id_cache:
            return self._player_id_cache[name]
        
        # Statiz 검색
        search_url = f"{STATIZ_BASE}/player/?m=search&name={name}"
        resp = self.safe_get(search_url)
        if not resp:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 검색 결과에서 첫 번째 선수 링크 추출
        # 실제 HTML 구조는 사이트에서 확인 필요
        player_link = soup.select_one("table tbody tr a[href*='p_no']")
        if not player_link:
            return None
        
        # href에서 p_no 추출
        href = player_link.get("href", "")
        import re
        match = re.search(r"p_no=(\d+)", href)
        if match:
            player_no = match.group(1)
            self._player_id_cache[name] = player_no
            self._save_cache()
            return player_no
        
        return None

    def fetch_pitcher_season_stats(self, player_no: str, season: int) -> Optional[dict]:
        """
        투수 시즌 통계 수집.
        Returns: {era, whip, fip, innings_pitched, strikeouts, walks, war_pitcher}
        """
        url = f"{STATIZ_BASE}/player/?m=playerinfo&p_no={player_no}&so={season}"
        resp = self.safe_get(url)
        if not resp:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 투수 스탯 테이블 파싱 (실제 셀렉터는 사이트에서 확인)
        stats_table = soup.select_one("table.player_info")
        if not stats_table:
            return None
        
        # 해당 시즌 행 찾기
        for row in stats_table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in row.select("td")]
            if not cells or cells[0] != str(season):
                continue
            
            try:
                return {
                    "era": float(cells[3]) if cells[3] else None,
                    "whip": float(cells[4]) if cells[4] else None,
                    "fip": float(cells[5]) if cells[5] else None,
                    "innings_pitched": float(cells[6]) if cells[6] else None,
                    "strikeouts": int(cells[7]) if cells[7] else None,
                    "walks": int(cells[8]) if cells[8] else None,
                    "war_pitcher": float(cells[9]) if cells[9] else None,
                }
            except (ValueError, IndexError):
                return None
        
        return None

    def sync_all_pitchers(self, db: Session, season: int) -> int:
        """
        roster.py에 정의된 모든 투수의 시즌 통계를 수집하여 DB에 저장.
        """
        from app.crawler.roster import get_all_pitchers
        from app.models.db.player import Player
        from app.models.db.team import Team
        from app.models.db.player_season_stats import PlayerSeasonStats
        
        if not self._logged_in:
            if not self.login():
                print("❌ 로그인 실패 — Statiz 동기화 중단")
                return 0
        
        pitchers = get_all_pitchers()
        saved_count = 0
        
        for pitcher_info in pitchers:
            name = pitcher_info["name"]
            
            # Statiz에서 player_no 검색
            player_no = self.search_player(name)
            if not player_no:
                print(f"⚠️ {name}: Statiz player_no 없음")
                continue
            
            # 시즌 통계 수집
            stats = self.fetch_pitcher_season_stats(player_no, season)
            if not stats:
                print(f"⚠️ {name}: {season}시즌 통계 없음")
                continue
            
            # DB에서 player 조회 (없으면 생성)
            team = db.query(Team).filter_by(
                short_name=pitcher_info["team_short_name"]
            ).first()
            if not team:
                continue
            
            player = db.query(Player).filter_by(
                name=name, team_id=team.id
            ).first()
            
            if not player:
                player = Player(
                    name=name,
                    team_id=team.id,
                    position=pitcher_info["position"],
                    throw_hand=pitcher_info.get("throw_hand"),
                    is_foreign=pitcher_info.get("is_foreign", False),
                )
                db.add(player)
                db.flush()
            
            # player_season_stats UPSERT
            existing = db.query(PlayerSeasonStats).filter_by(
                player_id=player.id, season=season
            ).first()
            
            if existing:
                for key, value in stats.items():
                    setattr(existing, key, value)
            else:
                pss = PlayerSeasonStats(player_id=player.id, season=season, **stats)
                db.add(pss)
            
            saved_count += 1
            print(f"✅ {name} ({season}): ERA {stats.get('era')}, WHIP {stats.get('whip')}")
        
        db.commit()
        return saved_count
```

##### `app/crawler/naver_crawler.py` — 선발 투수

```python
# backend/app/crawler/naver_crawler.py
"""
네이버 스포츠에서 당일 선발 투수 정보 수집.

선발 투수 확정 시간: 보통 경기 전날 저녁 ~ 당일 오전
확정 전: home_starter_id=NULL, confidence_level='LOW' 로 1차 예측 게시
확정 후: 18:00 크롤링에서 선발 투수 업데이트 + 예측 재실행

주의: 네이버 스포츠는 SPA(React 기반)이므로 일부 페이지는
Playwright 사용 필요.
"""
from bs4 import BeautifulSoup
from datetime import date
from typing import Optional

from app.crawler.base_crawler import BaseCrawler

NAVER_SPORTS_BASE = "https://sports.naver.com"


class NaverCrawler(BaseCrawler):
    
    def fetch_today_starters(self, target_date: date = None) -> list[dict]:
        """
        당일 선발 투수 정보 반환.
        
        Returns:
            [
                {
                    "game_date": "2025-05-12",
                    "home_team": "두산",
                    "away_team": "LG",
                    "home_starter": "곽빈",     # None이면 미확정
                    "away_starter": "임찬규",
                    "game_time": "18:30",
                },
                ...
            ]
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{NAVER_SPORTS_BASE}/kbaseball/schedule/index.nhn?date={date_str}"
        
        resp = self.safe_get(url)
        if not resp:
            return []
        
        # ⚠️ 네이버 스포츠가 SPA인 경우 requests로 안 될 수 있음
        # 그 경우 Playwright를 사용합니다 (아래 참고)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        games = []
        # 실제 CSS 셀렉터는 사이트 HTML 구조 확인 후 수정 필요
        for game_card in soup.select(".ScheduleLeagueType .GameItem"):
            try:
                home_team = game_card.select_one(".team_home .team_name")
                away_team = game_card.select_one(".team_away .team_name")
                
                home_starter_el = game_card.select_one(".team_home .pitcher_name")
                away_starter_el = game_card.select_one(".team_away .pitcher_name")
                
                games.append({
                    "game_date": date_str,
                    "home_team": home_team.get_text(strip=True) if home_team else None,
                    "away_team": away_team.get_text(strip=True) if away_team else None,
                    "home_starter": home_starter_el.get_text(strip=True) if home_starter_el else None,
                    "away_starter": away_starter_el.get_text(strip=True) if away_starter_el else None,
                })
            except Exception:
                continue
        
        return games

    def fetch_with_playwright(self, target_date: date = None) -> list[dict]:
        """
        Playwright를 사용한 SPA 크롤링 (JavaScript 렌더링 필요 시).
        
        사용 방법:
            crawler = NaverCrawler()
            games = crawler.fetch_with_playwright()
        """
        from playwright.sync_api import sync_playwright
        
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{NAVER_SPORTS_BASE}/kbaseball/schedule/index.nhn?date={date_str}"
        
        games = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            
            # 페이지 완전 로딩 대기
            page.wait_for_timeout(2000)
            
            # 게임 카드 파싱 (실제 셀렉터 확인 필요)
            game_cards = page.query_selector_all(".schedule_card")
            for card in game_cards:
                # ... 파싱 로직
                pass
            
            browser.close()
        
        return games
```

##### `app/crawler/weather_client.py` — 기상청 API

```python
# backend/app/crawler/weather_client.py
"""
기상청 Open API — 단기예보 조회.

API 신청: https://www.data.go.kr → "기상청_단기예보_((구)_동네예보)_조회서비스"
무료 1,000회/일 제공.

야외 구장만 날씨 적용 (고척스카이돔은 실내이므로 제외):
  - 잠실, 수원KT, 인천SSG, 창원NC, 광주기아, 사직, 대구삼성, 한화생명 → 날씨 영향 있음
  - 고척스카이돔 → is_dome=True, 날씨 무시
"""
from datetime import datetime
from typing import Optional

import requests
from app.config import settings

# 구장별 좌표 (기상청 격자 좌표)
STADIUM_COORDS = {
    "잠실야구장":             {"nx": 62, "ny": 126},
    "수원KT위즈파크":         {"nx": 60, "ny": 121},
    "인천SSG랜더스필드":       {"nx": 55, "ny": 124},
    "창원NC파크":             {"nx": 90, "ny": 91},
    "광주-기아챔피언스필드":   {"nx": 58, "ny": 74},
    "사직야구장":             {"nx": 98, "ny": 76},
    "대구삼성라이온즈파크":    {"nx": 89, "ny": 90},
    "한화생명이글스파크":      {"nx": 68, "ny": 100},
    # 돔 구장 (날씨 무관)
    "고척스카이돔":           None,
}


def fetch_weather(stadium: str, game_datetime: datetime) -> dict:
    """
    경기 당일 날씨 조회.
    
    Returns:
        {
            "pop": 30,            # 강수확률 (%)
            "wind_speed": 2.5,    # 풍속 (m/s)
            "temp": 18.0,         # 기온 (°C)
            "is_dome": False,     # 돔구장 여부
            "is_rain_risk": False # 강수확률 30% 이상 여부
        }
    """
    # 돔 구장 처리
    if STADIUM_COORDS.get(stadium) is None:
        return {
            "pop": 0,
            "wind_speed": 0.0,
            "temp": 22.0,
            "is_dome": True,
            "is_rain_risk": False,
        }
    
    if not settings.weather_api_key:
        return _default_weather()
    
    coords = STADIUM_COORDS.get(stadium)
    if not coords:
        return _default_weather()
    
    # 기상청 API 호출
    base_date = game_datetime.strftime("%Y%m%d")
    base_time = "0500"  # 05:00 발표 기준 (하루 전날 or 당일 새벽)
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": settings.weather_api_key,
        "pageNo": 1,
        "numOfRows": 100,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": coords["nx"],
        "ny": coords["ny"],
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        items = data["response"]["body"]["items"]["item"]
        
        pop = 0     # 강수확률
        wsd = 0.0   # 풍속
        tmp = 20.0  # 기온
        
        # 경기 시간대 예보 추출 (보통 18:00~21:00)
        game_hour = game_datetime.strftime("%H00")
        for item in items:
            if item["fcstTime"] == game_hour:
                if item["category"] == "POP":
                    pop = int(item["fcstValue"])
                elif item["category"] == "WSD":
                    wsd = float(item["fcstValue"])
                elif item["category"] == "TMP":
                    tmp = float(item["fcstValue"])
        
        return {
            "pop": pop,
            "wind_speed": wsd,
            "temp": tmp,
            "is_dome": False,
            "is_rain_risk": pop >= 30,
        }
    
    except Exception as e:
        print(f"기상청 API 오류: {e}")
        return _default_weather()


def _default_weather() -> dict:
    return {"pop": 0, "wind_speed": 0.0, "temp": 20.0, "is_dome": False, "is_rain_risk": False}
```

##### `app/crawler/pipeline.py` — 통합 파이프라인

```python
# backend/app/crawler/pipeline.py
"""
크롤링 통합 실행기. APScheduler에서 이 함수들을 호출합니다.

사용 방법 (수동 실행):
    python -c "
    from app.db.database import SessionLocal
    from app.crawler.pipeline import run_morning_pipeline
    db = SessionLocal()
    run_morning_pipeline(db)
    db.close()
    "
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.crawler.kbo_official_crawler import KBOOfficialCrawler
from app.crawler.statiz_crawler import StatizCrawler
from app.crawler.naver_crawler import NaverCrawler
from app.crawler.weather_client import fetch_weather
from app.utils.logger import logger


def run_morning_pipeline(db: Session) -> dict:
    """
    매일 06:00 실행.
    - 전날 경기 결과 + 팀 순위 수집 (KBO 공식)
    - 선수 시즌 통계 갱신 (Statiz)
    """
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    season = date.today().year
    
    results = {}
    
    # 1. 팀 순위 스냅샷 저장
    logger.info("📊 팀 순위 수집 시작...")
    kbo_crawler = KBOOfficialCrawler()
    try:
        count = kbo_crawler.save_team_snapshots(yesterday, db)
        results["team_snapshots"] = count
        kbo_crawler.log_crawl_result(
            db, "kbo_official", "team_rank", "SUCCESS", count
        )
        logger.info(f"✅ 팀 순위 {count}개 저장")
    except Exception as e:
        logger.error(f"❌ 팀 순위 수집 실패: {e}")
        kbo_crawler.log_crawl_result(
            db, "kbo_official", "team_rank", "FAILED", 0, str(e)
        )
    
    # 2. Statiz 투수 통계 갱신 (시즌 통계)
    logger.info("⚾ Statiz 투수 통계 수집 시작...")
    statiz = StatizCrawler()
    try:
        count = statiz.sync_all_pitchers(db, season)
        results["pitcher_stats"] = count
        statiz.log_crawl_result(
            db, "statiz", "pitcher_season_stats", "SUCCESS", count
        )
        logger.info(f"✅ 투수 통계 {count}명 저장")
    except Exception as e:
        logger.error(f"❌ Statiz 수집 실패: {e}")
        statiz.log_crawl_result(
            db, "statiz", "pitcher_season_stats", "FAILED", 0, str(e)
        )
    
    return results


def run_evening_pipeline(db: Session) -> dict:
    """
    매일 18:00 실행.
    - 당일 선발 투수 확정 정보 수집 (네이버)
    - 날씨 데이터 수집 (기상청)
    - 선발 미확정 경기는 confidence_level='LOW' 로 1차 예측 저장
    """
    logger.info("🌆 오후 파이프라인 시작...")
    naver = NaverCrawler()
    
    try:
        games = naver.fetch_today_starters()
        
        # 선발 투수 정보를 game_predictions에 업데이트
        # (상세 로직은 prediction_service.py에서 처리)
        from app.services.prediction_service import update_starters
        count = update_starters(games, db)
        
        logger.info(f"✅ 선발 투수 {count}경기 업데이트")
        return {"updated_games": count}
    
    except Exception as e:
        logger.error(f"❌ 오후 파이프라인 실패: {e}")
        return {"error": str(e)}


def run_bulk_historical_collection(
    start_date: str,
    end_date: str,
    db: Session,
) -> dict:
    """
    학습 데이터 구축을 위한 과거 데이터 일괄 수집.
    최초 1회만 실행. (예: 2023-01-01 ~ 2025-12-31)
    
    주의: 수천 번의 요청이 발생하므로 시간이 오래 걸립니다 (수 시간).
    밤새 실행하는 것을 권장합니다.
    """
    logger.info(f"📦 과거 데이터 수집 시작: {start_date} ~ {end_date}")
    
    kbo = KBOOfficialCrawler()
    result = kbo.bulk_collect_snapshots(start_date, end_date, db)
    
    logger.info(f"✅ 수집 완료: {result}")
    return result
```

---

### 3.2 ML/DL 파트 (B팀) 상세 가이드

#### 파일 구조 설명

```
backend/app/ml/
├── feature_engineering.py   ← 피처 생성 (as_of_date 기반 — 핵심!)
├── build_training_data.py   ← 학습 데이터셋 빌드 스크립트
├── xgboost_model.py         ← Stage 1: XGBoost 학습 & 저장
├── pytorch_model.py         ← Stage 2: LSTM 모델 정의 & 학습
├── ensemble.py              ← 앙상블 + 신뢰도 산정
├── backtest.py              ← 시점기반 백테스트
└── artifacts/               ← 학습된 모델 파일 (gitignore)
    ├── kbo_xgb_v1.pkl
    ├── kbo_lstm_v1.pt
    └── calibrator.pkl

notebooks/                   ← 분석 노트북
└── eda_and_backtest.ipynb
```

---

#### 파일별 구현 가이드

##### `app/ml/feature_engineering.py` — 피처 엔지니어링 (A↔B 핵심 인터페이스)

```python
# backend/app/ml/feature_engineering.py
"""
단일 경기에 대한 피처 벡터(47개) 생성.

★★★ 핵심 개념: as_of_date ★★★
  - as_of_date = '2024-05-01' 이면, 그 날짜까지만 알 수 있었던 정보만 사용
  - 학습 시: as_of_date = 경기일 - 1일 (미래 정보 누출 방지)
  - 추론 시: as_of_date = None → 현재 시점의 최신 데이터 사용

왜 이게 중요한가:
  - 잘못 구현 시: 백테스트 75% (비현실적) → 실전 50% (동전 던지기)
  - 올바르게 구현 시: 백테스트 58% → 실전도 비슷하게 나옴
"""
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.db.game import Game
from app.models.db.team import Team
from app.models.db.player import Player
from app.models.db.team_snapshot import TeamDailySnapshot
from app.models.db.player_season_stats import PlayerSeasonStats
from app.models.db.pitcher_game_stats import PitcherGameStats
from app.models.db.team_game_stats import TeamGameStats

# 피처 컬럼 순서 (반드시 유지 — B팀이 정의, A팀이 준수)
FEATURE_COLUMNS = [
    "home_season_win_rate", "away_season_win_rate",
    "home_last10_win_rate", "away_last10_win_rate",
    "home_home_win_rate", "away_away_win_rate",
    "home_streak", "away_streak",
    "home_ops", "away_ops",
    "home_era", "away_era",
    "home_run_diff_last10", "away_run_diff_last10",
    "home_starter_era", "away_starter_era",
    "home_starter_recent5_era", "away_starter_recent5_era",
    "home_starter_whip", "away_starter_whip",
    "home_bullpen_era", "away_bullpen_era",
    "home_top5_ops", "away_top5_ops",
    "home_hr_power", "away_hr_power",
    "h2h_home_win_rate",
    "rest_diff", "is_weekend", "is_dome",
    "era_diff", "ops_diff", "last10_wr_diff",
    "season_wr_diff", "starter_era_diff",
    "bullpen_era_diff", "top5_ops_diff",
    "streak_diff", "home_win_rate_diff",
    "run_diff_diff", "hr_power_diff",
    "pitcher_whip_diff", "pitcher_recent5_era_diff",
    "h2h_diff",
]


def build_features_for_game(
    game_id: int,
    *,
    as_of_date: Optional[date] = None,
    db: Session,
) -> pd.DataFrame:
    """
    단일 경기에 대해 피처 1행 생성.
    
    Args:
        game_id: 경기 ID
        as_of_date: 이 날짜까지의 정보만 사용 (None이면 최신 정보)
        db: SQLAlchemy 세션
    
    Returns:
        DataFrame shape (1, 47) — FEATURE_COLUMNS 순서
    """
    game = db.query(Game).get(game_id)
    if not game:
        raise ValueError(f"game_id={game_id} 없음")
    
    # cutoff: 이 날짜까지의 정보만 사용
    if as_of_date:
        cutoff = as_of_date
    else:
        cutoff = game.scheduled_at.date() - timedelta(days=1)
    
    # 팀 스냅샷 조회 (cutoff 이전 가장 최근 값)
    home_snap = _get_team_snapshot(game.home_team_id, cutoff, db)
    away_snap = _get_team_snapshot(game.away_team_id, cutoff, db)
    
    # 선발 투수 통계
    prediction = _get_prediction(game_id, db)
    home_pitcher_id = prediction.home_starter_id if prediction else None
    away_pitcher_id = prediction.away_starter_id if prediction else None
    
    home_pitcher_stats = _get_pitcher_stats(home_pitcher_id, game.season, cutoff, db)
    away_pitcher_stats = _get_pitcher_stats(away_pitcher_id, game.season, cutoff, db)
    
    # 팀 타선 통계
    home_team_stats = _get_team_season_stats(game.home_team_id, game.season, db)
    away_team_stats = _get_team_season_stats(game.away_team_id, game.season, db)
    
    # 최근 10경기 평균 득점/실점 차이
    home_run_diff = _get_run_diff_last10(game.home_team_id, cutoff, db)
    away_run_diff = _get_run_diff_last10(game.away_team_id, cutoff, db)
    
    # H2H 승률
    h2h = _get_h2h_win_rate(game.home_team_id, game.away_team_id, cutoff, db)
    
    # 휴식일 차이
    rest_diff = _get_rest_diff(game, cutoff, db)
    
    # 주말 여부, 돔구장 여부
    is_weekend = 1 if game.scheduled_at.weekday() >= 5 else 0
    is_dome = 1 if game.stadium == "고척스카이돔" else 0
    
    # ── 피처 딕셔너리 구성 ──
    home_season_wr = home_snap.season_win_rate if home_snap else 0.5
    away_season_wr = away_snap.season_win_rate if away_snap else 0.5
    home_last10_wr = (home_snap.last10_wins / 10) if home_snap and home_snap.last10_wins is not None else 0.5
    away_last10_wr = (away_snap.last10_wins / 10) if away_snap and away_snap.last10_wins is not None else 0.5
    
    # streak: 연승은 양수, 연패는 음수
    home_streak_val = (home_snap.streak_count if home_snap.streak_type == "WIN" else -home_snap.streak_count) if home_snap else 0
    away_streak_val = (away_snap.streak_count if away_snap.streak_type == "WIN" else -away_snap.streak_count) if away_snap else 0
    
    home_ops = home_team_stats.team_ops if home_team_stats else 0.720
    away_ops = away_team_stats.team_ops if away_team_stats else 0.720
    home_era = home_team_stats.team_era if home_team_stats else 4.50
    away_era = away_team_stats.team_era if away_team_stats else 4.50
    
    home_starter_era = float(home_pitcher_stats.era) if home_pitcher_stats and home_pitcher_stats.era else home_era
    away_starter_era = float(away_pitcher_stats.era) if away_pitcher_stats and away_pitcher_stats.era else away_era
    home_starter_recent5_era = _get_pitcher_recent5_era(home_pitcher_id, cutoff, db)
    away_starter_recent5_era = _get_pitcher_recent5_era(away_pitcher_id, cutoff, db)
    home_starter_whip = float(home_pitcher_stats.whip) if home_pitcher_stats and home_pitcher_stats.whip else 1.30
    away_starter_whip = float(away_pitcher_stats.whip) if away_pitcher_stats and away_pitcher_stats.whip else 1.30
    
    features = {
        "home_season_win_rate": home_season_wr,
        "away_season_win_rate": away_season_wr,
        "home_last10_win_rate": home_last10_wr,
        "away_last10_win_rate": away_last10_wr,
        "home_home_win_rate": _get_home_away_win_rate(game.home_team_id, "home", cutoff, db),
        "away_away_win_rate": _get_home_away_win_rate(game.away_team_id, "away", cutoff, db),
        "home_streak": home_streak_val,
        "away_streak": away_streak_val,
        "home_ops": float(home_ops) if home_ops else 0.720,
        "away_ops": float(away_ops) if away_ops else 0.720,
        "home_era": float(home_era) if home_era else 4.50,
        "away_era": float(away_era) if away_era else 4.50,
        "home_run_diff_last10": home_run_diff,
        "away_run_diff_last10": away_run_diff,
        "home_starter_era": home_starter_era,
        "away_starter_era": away_starter_era,
        "home_starter_recent5_era": home_starter_recent5_era,
        "away_starter_recent5_era": away_starter_recent5_era,
        "home_starter_whip": home_starter_whip,
        "away_starter_whip": away_starter_whip,
        "home_bullpen_era": _get_bullpen_era(game.home_team_id, home_pitcher_id, game.season, db),
        "away_bullpen_era": _get_bullpen_era(game.away_team_id, away_pitcher_id, game.season, db),
        "home_top5_ops": 0.720,    # TODO: 타자 데이터 수집 후 구현
        "away_top5_ops": 0.720,
        "home_hr_power": 0,        # TODO: 팀 홈런 수 수집 후 구현
        "away_hr_power": 0,
        "h2h_home_win_rate": h2h,
        "rest_diff": rest_diff,
        "is_weekend": is_weekend,
        "is_dome": is_dome,
        # ── 차이값 피처 (diff) ──
        "era_diff": away_starter_era - home_starter_era,
        "ops_diff": float(home_ops or 0.720) - float(away_ops or 0.720),
        "last10_wr_diff": home_last10_wr - away_last10_wr,
        "season_wr_diff": home_season_wr - away_season_wr,
        "starter_era_diff": away_starter_era - home_starter_era,
        "bullpen_era_diff": 0.0,   # TODO
        "top5_ops_diff": 0.0,
        "streak_diff": home_streak_val - away_streak_val,
        "home_win_rate_diff": _get_home_away_win_rate(game.home_team_id, "home", cutoff, db) - _get_home_away_win_rate(game.away_team_id, "away", cutoff, db),
        "run_diff_diff": home_run_diff - away_run_diff,
        "hr_power_diff": 0.0,
        "pitcher_whip_diff": away_starter_whip - home_starter_whip,
        "pitcher_recent5_era_diff": away_starter_recent5_era - home_starter_recent5_era,
        "h2h_diff": h2h - 0.5,
    }
    
    return pd.DataFrame([features])[FEATURE_COLUMNS]


# ── 헬퍼 함수들 ──

def _get_team_snapshot(team_id: int, cutoff: date, db: Session):
    return (
        db.query(TeamDailySnapshot)
        .filter(
            TeamDailySnapshot.team_id == team_id,
            TeamDailySnapshot.snapshot_date <= cutoff,
        )
        .order_by(TeamDailySnapshot.snapshot_date.desc())
        .first()
    )


def _get_pitcher_stats(player_id: Optional[int], season: int, cutoff: date, db: Session):
    if not player_id:
        return None
    return db.query(PlayerSeasonStats).filter_by(player_id=player_id, season=season).first()


def _get_pitcher_recent5_era(player_id: Optional[int], cutoff: date, db: Session) -> float:
    if not player_id:
        return 4.50
    stats = (
        db.query(PitcherGameStats)
        .join(Game, PitcherGameStats.game_id == Game.id)
        .filter(
            PitcherGameStats.player_id == player_id,
            Game.scheduled_at <= cutoff,
            PitcherGameStats.is_starter == True,
        )
        .order_by(Game.scheduled_at.desc())
        .limit(5)
        .all()
    )
    if not stats:
        return 4.50
    eras = [float(s.era) for s in stats if s.era is not None]
    return sum(eras) / len(eras) if eras else 4.50


def _get_team_season_stats(team_id: int, season: int, db: Session):
    from app.models.db.team_season_stats import TeamSeasonStats
    return db.query(TeamSeasonStats).filter_by(team_id=team_id, season=season).first()


def _get_run_diff_last10(team_id: int, cutoff: date, db: Session) -> float:
    recent = (
        db.query(TeamGameStats)
        .join(Game, TeamGameStats.game_id == Game.id)
        .filter(
            TeamGameStats.team_id == team_id,
            Game.scheduled_at <= cutoff,
            Game.status == "COMPLETED",
        )
        .order_by(Game.scheduled_at.desc())
        .limit(10)
        .all()
    )
    if not recent:
        return 0.0
    diffs = [float(s.runs_scored or 0) for s in recent]
    return sum(diffs) / len(diffs)


def _get_h2h_win_rate(home_team_id: int, away_team_id: int, cutoff: date, db: Session) -> float:
    games = (
        db.query(Game)
        .filter(
            Game.home_team_id == home_team_id,
            Game.away_team_id == away_team_id,
            Game.scheduled_at <= cutoff,
            Game.status == "COMPLETED",
        )
        .order_by(Game.scheduled_at.desc())
        .limit(20)
        .all()
    )
    if not games:
        return 0.5
    wins = sum(1 for g in games if g.home_score > g.away_score)
    return wins / len(games)


def _get_rest_diff(game: Game, cutoff: date, db: Session) -> int:
    def last_game_date(team_id):
        g = (
            db.query(Game)
            .filter(
                ((Game.home_team_id == team_id) | (Game.away_team_id == team_id)),
                Game.game_id != game.id,
                Game.scheduled_at < game.scheduled_at,
                Game.status == "COMPLETED",
            )
            .order_by(Game.scheduled_at.desc())
            .first()
        )
        return g.scheduled_at.date() if g else None
    
    home_last = last_game_date(game.home_team_id)
    away_last = last_game_date(game.away_team_id)
    
    home_rest = (game.scheduled_at.date() - home_last).days if home_last else 3
    away_rest = (game.scheduled_at.date() - away_last).days if away_last else 3
    return home_rest - away_rest


def _get_home_away_win_rate(team_id: int, location: str, cutoff: date, db: Session) -> float:
    is_home = location == "home"
    condition = Game.home_team_id == team_id if is_home else Game.away_team_id == team_id
    games = (
        db.query(Game)
        .filter(condition, Game.scheduled_at <= cutoff, Game.status == "COMPLETED")
        .all()
    )
    if not games:
        return 0.5
    if is_home:
        wins = sum(1 for g in games if g.home_score > g.away_score)
    else:
        wins = sum(1 for g in games if g.away_score > g.home_score)
    return wins / len(games)


def _get_prediction(game_id: int, db: Session):
    from app.models.db.prediction import GamePrediction
    return (
        db.query(GamePrediction)
        .filter_by(game_id=game_id, is_final=True)
        .order_by(GamePrediction.predicted_at.desc())
        .first()
    )


def _get_bullpen_era(team_id: int, starter_id: Optional[int], season: int, db: Session) -> float:
    """선발 제외 불펜 ERA"""
    from app.models.db.player_season_stats import PlayerSeasonStats
    from app.models.db.player import Player
    
    pitchers = db.query(Player).filter_by(team_id=team_id, position="PITCHER", is_active=True).all()
    eras = []
    for p in pitchers:
        if p.id == starter_id:
            continue
        stats = db.query(PlayerSeasonStats).filter_by(player_id=p.id, season=season).first()
        if stats and stats.era and float(stats.era) < 10.0:
            eras.append(float(stats.era))
    return sum(eras) / len(eras) if eras else 4.50
```

##### `app/ml/build_training_data.py` — 학습 데이터 빌드

```python
# backend/app/ml/build_training_data.py
"""
학습 데이터셋 빌드 스크립트.
완료된 모든 경기에 대해 피처(47개) + 레이블(홈승=1, 원정승=0) 생성.

실행 방법:
    python -m app.ml.build_training_data

예상 실행 시간: 3시즌 × 720경기 = 2,160경기 × 피처 계산 ≈ 30분~1시간
"""
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Django-style: backend/ 폴더를 루트로 실행
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.db.database import SessionLocal
from app.models.db.game import Game
from app.ml.feature_engineering import build_features_for_game

OUTPUT_PATH = Path("data/training_set.parquet")


def build_training_dataset(
    seasons: list[int] = [2023, 2024, 2025],
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """
    모든 완료 경기에 대해 피처 + 레이블 생성.
    
    주의: as_of_date = 경기일 - 1일 (look-ahead bias 방지)
    """
    db = SessionLocal()
    rows = []
    failed = 0
    
    try:
        games = (
            db.query(Game)
            .filter(
                Game.season.in_(seasons),
                Game.status == "COMPLETED",
            )
            .order_by(Game.scheduled_at)
            .all()
        )
        
        print(f"📊 총 {len(games)}경기 피처 생성 시작...")
        
        for game in tqdm(games, desc="피처 생성"):
            try:
                # ★ 핵심: 경기일 전날까지의 정보만 사용
                as_of = game.scheduled_at.date() - timedelta(days=1)
                
                features = build_features_for_game(game.id, as_of_date=as_of, db=db)
                
                # 레이블: 홈팀 승리 = 1, 원정팀 승리 = 0
                label = 1 if game.home_score > game.away_score else 0
                features["label"] = label
                features["game_id"] = game.id
                features["scheduled_at"] = game.scheduled_at
                features["season"] = game.season
                
                rows.append(features)
            
            except Exception as e:
                failed += 1
                # print(f"❌ game_id={game.id}: {e}")
        
        df = pd.concat(rows, ignore_index=True)
        
        # Parquet으로 저장 (CSV보다 빠르고 용량 작음)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path)
        
        print(f"\n✅ 학습 데이터 생성 완료!")
        print(f"   - 총 경기: {len(games)}")
        print(f"   - 성공: {len(df)}")
        print(f"   - 실패: {failed}")
        print(f"   - 홈팀 승률: {df['label'].mean():.3f} (0.5에 가까울수록 좋음)")
        print(f"   - 저장: {output_path}")
        
        return df
    
    finally:
        db.close()


if __name__ == "__main__":
    build_training_dataset()
```

##### `app/ml/xgboost_model.py` — XGBoost Stage 1

```python
# backend/app/ml/xgboost_model.py
"""
Stage 1: XGBoost 이진 분류 모델.

학습 방법:
    python -m app.ml.xgboost_model

목표 성능:
  - MVP: Test Accuracy ≥ 55%, LogLoss ≤ 0.69
  - 최종: Accuracy ≥ 58%, LogLoss ≤ 0.65

★★★ 절대 금지: train_test_split(shuffle=True) ★★★
  → 시간 기준 분할만 사용 (미래 경기로 과거를 예측하면 안 됨)
"""
import sys
from pathlib import Path

import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.isotonic import IsotonicRegression
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.ml.feature_engineering import FEATURE_COLUMNS

ARTIFACT_DIR = Path("app/ml/artifacts")
TRAINING_DATA_PATH = Path("data/training_set.parquet")


def train_xgboost(data_path: Path = TRAINING_DATA_PATH) -> dict:
    """
    XGBoost 모델 학습 & 저장.
    
    시간 기준 분할:
      Train: 70% (2023 전체 + 2024 초반)
      Val:   15% (2024 후반)
      Test:  15% (2025 — 실전과 가장 유사)
    """
    print("📂 학습 데이터 로드 중...")
    df = pd.read_parquet(data_path)
    
    # ★ 시간 기준 정렬 (필수!)
    df = df.sort_values("scheduled_at").reset_index(drop=True)
    
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    
    print(f"  Train: {len(train)}경기 ({train['scheduled_at'].min().date()} ~ {train['scheduled_at'].max().date()})")
    print(f"  Val:   {len(val)}경기 ({val['scheduled_at'].min().date()} ~ {val['scheduled_at'].max().date()})")
    print(f"  Test:  {len(test)}경기 ({test['scheduled_at'].min().date()} ~ {test['scheduled_at'].max().date()})")
    
    # 모델 정의
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        early_stopping_rounds=30,
        random_state=42,
        tree_method="hist",
        verbosity=0,
    )
    
    print("\n🚀 XGBoost 학습 시작...")
    model.fit(
        train[FEATURE_COLUMNS], train["label"],
        eval_set=[(val[FEATURE_COLUMNS], val["label"])],
        verbose=50,
    )
    
    # 평가
    test_proba = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    test_pred = (test_proba > 0.5).astype(int)
    
    test_acc = accuracy_score(test["label"], test_pred)
    test_logloss = log_loss(test["label"], test_proba)
    test_brier = brier_score_loss(test["label"], test_proba)
    
    print(f"\n📊 Test 성능:")
    print(f"  Accuracy: {test_acc:.4f} (목표: ≥ 0.55)")
    print(f"  LogLoss:  {test_logloss:.4f} (목표: ≤ 0.69)")
    print(f"  Brier:    {test_brier:.4f}")
    
    # Calibration (확률 보정)
    val_proba = model.predict_proba(val[FEATURE_COLUMNS])[:, 1]
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(val_proba, val["label"])
    
    # Feature Importance 출력 (상위 15개)
    feature_importance = pd.Series(
        model.feature_importances_,
        index=FEATURE_COLUMNS,
    ).sort_values(ascending=False)
    print(f"\n📈 Feature Importance Top 15:")
    print(feature_importance.head(15).to_string())
    
    # 모델 저장
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    artifact = {
        "model": model,
        "features": FEATURE_COLUMNS,
        "model_name": "xgboost_v1",
        "version": "v1.0",
        "label_map": {0: "AWAY_WIN", 1: "HOME_WIN"},
        "needs_scale": False,
        "scaler": None,
        "calibrator": calibrator,
        "trained_at": datetime.now().isoformat(),
        "test_accuracy": float(test_acc),
        "test_logloss": float(test_logloss),
        "test_brier": float(test_brier),
        "train_size": len(train),
        "val_size": len(val),
        "test_size": len(test),
    }
    
    artifact_path = ARTIFACT_DIR / "kbo_xgb_v1.pkl"
    joblib.dump(artifact, artifact_path)
    
    # Calibrator도 별도 저장 (ensemble에서 사용)
    joblib.dump(calibrator, ARTIFACT_DIR / "calibrator.pkl")
    
    print(f"\n✅ 모델 저장 완료: {artifact_path}")
    
    return {
        "accuracy": test_acc,
        "logloss": test_logloss,
        "brier": test_brier,
        "artifact_path": str(artifact_path),
    }


if __name__ == "__main__":
    result = train_xgboost()
    if result["accuracy"] < 0.55:
        print("⚠️ 목표 정확도 미달 — 피처 엔지니어링 또는 하이퍼파라미터 재검토 필요")
```

##### `app/ml/pytorch_model.py` — LSTM Stage 2

```python
# backend/app/ml/pytorch_model.py
"""
Stage 2: LSTM + MLP 하이브리드 모델.

입력:
  - 시계열 (LSTM): 선발 투수 최근 5경기, 팀 최근 10경기
  - 정적 (MLP): 누적 피처 30개

목표: XGBoost와 앙상블하여 logloss 개선

주의: 샘플 수(2,160)가 적으므로 Dropout, Early Stopping 필수
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path


class KBOPredictionModel(nn.Module):
    """
    LSTM + MLP 하이브리드.
    
    홈/원정 선발 투수 최근 5경기(시계열) + 팀 최근 10경기(시계열) +
    정적 피처 30개를 결합하여 홈팀 승리 확률 출력.
    """
    
    def __init__(
        self,
        pitcher_seq_len: int = 5,
        pitcher_feat_dim: int = 5,   # ERA, WHIP, K, IP, ER
        team_seq_len: int = 10,
        team_feat_dim: int = 4,       # 득점, 실점, 승패, 홈여부
        static_dim: int = 30,
        hidden: int = 64,
        dropout: float = 0.3,
    ):
        super().__init__()
        
        # 선발 투수 LSTM (홈/원정 공유 파라미터)
        self.pitcher_lstm = nn.LSTM(
            input_size=pitcher_feat_dim,
            hidden_size=hidden,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
        )
        
        # 팀 폼 LSTM (홈/원정 공유 파라미터)
        self.team_lstm = nn.LSTM(
            input_size=team_feat_dim,
            hidden_size=hidden,
            num_layers=1,
            batch_first=True,
        )
        
        # 정적 피처 MLP
        self.static_mlp = nn.Sequential(
            nn.Linear(static_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        
        # 결합 후 분류 헤드
        # hidden * 5 = 홈투수 + 원정투수 + 홈팀 + 원정팀 + 정적
        self.head = nn.Sequential(
            nn.Linear(hidden * 5, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )
    
    def forward(
        self,
        home_pitcher: torch.Tensor,   # (batch, 5, 5)
        away_pitcher: torch.Tensor,   # (batch, 5, 5)
        home_team: torch.Tensor,      # (batch, 10, 4)
        away_team: torch.Tensor,      # (batch, 10, 4)
        static: torch.Tensor,         # (batch, 30)
    ) -> torch.Tensor:
        
        _, (h_hp, _) = self.pitcher_lstm(home_pitcher)
        _, (h_ap, _) = self.pitcher_lstm(away_pitcher)
        _, (h_ht, _) = self.team_lstm(home_team)
        _, (h_at, _) = self.team_lstm(away_team)
        h_st = self.static_mlp(static)
        
        combined = torch.cat([
            h_hp.squeeze(0),
            h_ap.squeeze(0),
            h_ht.squeeze(0),
            h_at.squeeze(0),
            h_st,
        ], dim=1)
        
        logit = self.head(combined)
        return torch.sigmoid(logit).squeeze(-1)


class KBODataset(Dataset):
    """
    PyTorch Dataset 클래스.
    시계열 + 정적 피처 배치 생성.
    """
    
    def __init__(self, data: list[dict]):
        """
        data: [
            {
                "home_pitcher": np.array (5, 5),
                "away_pitcher": np.array (5, 5),
                "home_team": np.array (10, 4),
                "away_team": np.array (10, 4),
                "static": np.array (30,),
                "label": int (0 or 1),
            },
            ...
        ]
        """
        self.data = data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            "home_pitcher": torch.FloatTensor(item["home_pitcher"]),
            "away_pitcher": torch.FloatTensor(item["away_pitcher"]),
            "home_team":    torch.FloatTensor(item["home_team"]),
            "away_team":    torch.FloatTensor(item["away_team"]),
            "static":       torch.FloatTensor(item["static"]),
            "label":        torch.FloatTensor([item["label"]]),
        }


def train_pytorch_model(
    train_data: list[dict],
    val_data: list[dict],
    model_config: dict = None,
    epochs: int = 50,
    patience: int = 10,
) -> KBOPredictionModel:
    """
    LSTM 모델 학습.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔧 디바이스: {device}")
    
    config = model_config or {}
    model = KBOPredictionModel(**config).to(device)
    
    train_loader = DataLoader(KBODataset(train_data), batch_size=32, shuffle=True)
    val_loader = DataLoader(KBODataset(val_data), batch_size=32, shuffle=False)
    
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.BCELoss()
    
    best_val_loss = float("inf")
    patience_counter = 0
    best_state = None
    
    print(f"🚀 LSTM 학습 시작... (최대 {epochs} 에폭)")
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            
            inputs = {k: v.to(device) for k, v in batch.items() if k != "label"}
            labels = batch["label"].squeeze(-1).to(device)
            
            pred = model(**inputs)
            loss = criterion(pred, labels)
            loss.backward()
            
            # Gradient clipping (학습 안정화)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                inputs = {k: v.to(device) for k, v in batch.items() if k != "label"}
                labels = batch["label"].squeeze(-1).to(device)
                pred = model(**inputs)
                val_loss += criterion(pred, labels).item()
        
        val_loss /= len(val_loader)
        train_loss /= len(train_loader)
        scheduler.step()
        
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch + 1}/{epochs} — Train: {train_loss:.4f}, Val: {val_loss:.4f}")
        
        # Early Stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch + 1}")
                break
    
    # 최적 가중치 복원
    if best_state:
        model.load_state_dict(best_state)
    
    # 모델 저장
    artifact_dir = Path("app/ml/artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    artifact = {
        "model_state_dict": model.state_dict(),
        "model_config": config,
        "version": "v1.0-lstm",
        "best_val_loss": best_val_loss,
    }
    torch.save(artifact, artifact_dir / "kbo_lstm_v1.pt")
    print(f"✅ LSTM 모델 저장: app/ml/artifacts/kbo_lstm_v1.pt")
    
    return model
```

##### `app/ml/ensemble.py` — 앙상블 로직

```python
# backend/app/ml/ensemble.py
"""
XGBoost + LSTM 앙상블.
신뢰도 기반 동적 가중치 적용.
"""


def ensemble_prediction(
    xgb_proba: float,
    lstm_proba: float,
    context: dict,
) -> dict:
    """
    두 모델의 예측을 앙상블하여 최종 확률 및 신뢰도 반환.
    
    Args:
        xgb_proba: XGBoost 홈팀 승리 확률 (보정 후)
        lstm_proba: LSTM 홈팀 승리 확률
        context:
            - starter_unconfirmed: bool (선발 미확정 시 True)
    
    Returns:
        {
            "home_win_prob": 0.62,
            "away_win_prob": 0.38,
            "confidence_level": "HIGH",
            "xgboost_home_prob": 0.61,
            "lstm_home_prob": 0.64,
            "weights": {"xgb": 0.6, "lstm": 0.4},
        }
    """
    w_xgb = 0.6
    w_lstm = 0.4
    
    diff = abs(xgb_proba - lstm_proba)
    
    # 두 모델 차이가 크면 LSTM 가중치 감소
    if diff > 0.20:
        w_xgb = 0.75
        w_lstm = 0.25
    
    # 선발 미확정 시 XGBoost만 사용 (팀 통계 기반)
    if context.get("starter_unconfirmed"):
        w_xgb = 1.0
        w_lstm = 0.0
    
    final = w_xgb * xgb_proba + w_lstm * lstm_proba
    final = max(0.05, min(0.95, final))  # 극단값 방지
    
    # 신뢰도 산정
    distance_from_50 = abs(final - 0.5)
    agreement = 1.0 - diff
    confidence_score = distance_from_50 * agreement
    
    if confidence_score > 0.12:
        confidence = "HIGH"
    elif confidence_score > 0.06:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    # 선발 미확정 시 최대 MEDIUM
    if context.get("starter_unconfirmed") and confidence == "HIGH":
        confidence = "MEDIUM"
    
    return {
        "home_win_prob": round(final, 4),
        "away_win_prob": round(1.0 - final, 4),
        "confidence_level": confidence,
        "xgboost_home_prob": round(xgb_proba, 4),
        "lstm_home_prob": round(lstm_proba, 4),
        "weights": {"xgb": w_xgb, "lstm": w_lstm},
    }
```

##### `app/ml/backtest.py` — 시점기반 백테스트

```python
# backend/app/ml/backtest.py
"""
시점기반 백테스트.

"매일 그날까지의 정보만으로 그날 경기를 예측" 하는 시뮬레이션.
단순 test set 정확도가 아닌 실전과 동일한 조건으로 검증.

실행:
    python -m app.ml.backtest
"""
import sys
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.db.database import SessionLocal
from app.models.db.game import Game
from app.ml.feature_engineering import build_features_for_game, FEATURE_COLUMNS


def time_based_backtest(
    start_date: date,
    end_date: date,
    artifact_path: str = "app/ml/artifacts/kbo_xgb_v1.pkl",
) -> dict:
    """
    시점기반 백테스트.
    각 날짜에 대해, 그 날짜의 D-1 시점 피처로 D일 경기 예측 → 실제 결과와 비교.
    """
    print(f"🔍 백테스트 기간: {start_date} ~ {end_date}")
    
    artifact = joblib.load(artifact_path)
    model = artifact["model"]
    calibrator = artifact.get("calibrator")
    
    db = SessionLocal()
    results = []
    
    try:
        current = start_date
        while current <= end_date:
            games = (
                db.query(Game)
                .filter(
                    Game.scheduled_at >= current,
                    Game.scheduled_at < current + timedelta(days=1),
                    Game.status == "COMPLETED",
                )
                .all()
            )
            
            for g in games:
                try:
                    # D-1 시점 피처
                    X = build_features_for_game(
                        g.id,
                        as_of_date=current - timedelta(days=1),
                        db=db,
                    )
                    
                    raw_proba = model.predict_proba(X[FEATURE_COLUMNS])[0, 1]
                    
                    # Calibration 적용
                    if calibrator:
                        pred_proba = calibrator.predict([raw_proba])[0]
                    else:
                        pred_proba = raw_proba
                    
                    actual = 1 if g.home_score > g.away_score else 0
                    dist = abs(pred_proba - 0.5)
                    confidence = "HIGH" if dist > 0.15 else "MEDIUM" if dist > 0.08 else "LOW"
                    
                    results.append({
                        "date": current,
                        "game_id": g.id,
                        "predicted_home_prob": pred_proba,
                        "predicted": int(pred_proba > 0.5),
                        "actual": actual,
                        "correct": int(pred_proba > 0.5) == actual,
                        "confidence": confidence,
                    })
                
                except Exception as e:
                    pass
            
            current += timedelta(days=1)
    
    finally:
        db.close()
    
    df = pd.DataFrame(results)
    
    if df.empty:
        print("❌ 백테스트 데이터 없음")
        return {}
    
    report = {
        "total_games": len(df),
        "overall_accuracy": float(df["correct"].mean()),
        "high_conf_count": int((df["confidence"] == "HIGH").sum()),
        "high_conf_accuracy": float(df[df["confidence"] == "HIGH"]["correct"].mean()) if (df["confidence"] == "HIGH").any() else None,
        "medium_conf_accuracy": float(df[df["confidence"] == "MEDIUM"]["correct"].mean()) if (df["confidence"] == "MEDIUM").any() else None,
        "low_conf_accuracy": float(df[df["confidence"] == "LOW"]["correct"].mean()) if (df["confidence"] == "LOW").any() else None,
    }
    
    print(f"\n📊 백테스트 결과:")
    print(f"  전체 경기: {report['total_games']}")
    print(f"  전체 정확도: {report['overall_accuracy']:.4f} ({report['overall_accuracy']*100:.1f}%)")
    print(f"  HIGH 신뢰도 정확도: {report.get('high_conf_accuracy', 'N/A')}")
    print(f"  MEDIUM 신뢰도 정확도: {report.get('medium_conf_accuracy', 'N/A')}")
    
    if report["overall_accuracy"] > 0.65:
        print("\n⚠️ 경고: 백테스트 정확도가 65% 초과 — look-ahead bias 의심!")
        print("   as_of_date가 올바르게 적용되었는지 feature_engineering.py를 재확인하세요.")
    
    return report


if __name__ == "__main__":
    result = time_based_backtest(
        start_date=date(2025, 4, 1),
        end_date=date(2025, 5, 12),
    )
```

---

### 3.3 협업 가이드

#### A↔B 팀 공유 인터페이스 체크포인트

| 시점 | A팀이 전달 | B팀이 확인 |
|------|-----------|-----------|
| Day 1 | DB 스키마 추가 테이블 적용 완료 | DB 접속 후 테이블 존재 확인 |
| Day 2 | 게임 데이터 최소 500경기 이상 적재 | `build_training_dataset()` 소량으로 테스트 |
| Day 3 | 3시즌 팀 스냅샷 수집 완료 | 피처 계산 테스트 (`build_features_for_game`) |
| Day 4 | `FEATURE_COLUMNS` 47개 모두 정상 생성 확인 | XGBoost 학습 시작 |
| Day 5 | 선발 투수 데이터 수집 완료 | 앙상블 + `predict_game()` 백엔드 전달 |

#### 컨벤션

```python
# ✅ 함수 docstring 필수 (헬퍼 함수 제외)
def build_features_for_game(game_id: int, *, as_of_date=None, db) -> pd.DataFrame:
    """단일 경기 피처 생성. as_of_date 기준 정보만 사용."""
    ...

# ✅ 에러 시 print 대신 logger 사용
from loguru import logger
logger.error(f"크롤링 실패: {e}")

# ✅ DB 세션은 with문 또는 finally로 반드시 닫기
db = SessionLocal()
try:
    ...
finally:
    db.close()
```

#### 브랜치 전략 (3.3절 참고)

```bash
# AI 파트 공통
git checkout -b feat/crawler-base       # base_crawler
git checkout -b feat/crawler-kbo        # KBO 공식
git checkout -b feat/crawler-statiz     # Statiz
git checkout -b feat/ml-features        # feature_engineering
git checkout -b feat/ml-xgboost         # XGBoost
git checkout -b feat/ml-lstm            # PyTorch
git checkout -b feat/ml-ensemble        # 앙상블
```

---

## 4. 일정 및 계획표

### 7일 스프린트 (AI & 크롤링 파트)

| 일차 | A팀 (크롤링) | B팀 (ML/DL) | 완료 기준 |
|------|-------------|-------------|-----------|
| **Day 1** | `base_crawler.py` 구현 | 피처 카탈로그 47개 확정 (문서 리뷰) | 크롤러 베이스 동작 확인 |
| | `roster.py` 10개 팀 로스터 작성 | `feature_engineering.py` 스켈레톤 함수 시그니처 작성 | 양쪽 파일 GitHub에 올라감 |
| | KBO 공식 크롤러 구현 시작 | EDA 노트북 시작 (기존 데이터 샘플 분석) | |
| **Day 2** | KBO 공식 크롤러 완성 | `build_training_data.py` 구현 | games 테이블 최소 500경기 |
| | 2023~2025 팀 순위 스냅샷 수집 (bulk) | A팀 일부 데이터로 `build_training_dataset()` 테스트 | team_daily_snapshots 데이터 있음 |
| | Statiz 크롤러 구현 시작 | 피처 생성 E2E 테스트 1경기 | |
| **Day 3** | Statiz 크롤러 완성 + 투수 통계 수집 | XGBoost 첫 학습 실행 | Test Accuracy ≥ 55% |
| | 네이버 크롤러 구현 | 피처 중요도 분석 (불필요 피처 제거) | |
| | `weather_client.py` 구현 | Optuna 하이퍼파라미터 튜닝 시작 | |
| **Day 4** | 스케줄러 연동 (`pipeline.py` 완성) | LSTM 모델 코드 작성 | 스케줄러 3개 태스크 등록 |
| | 데이터 품질 최종 검증 | LSTM 학습 첫 시도 | XGBoost 58%+ 달성 |
| | B팀 지원 (피처 계산 디버깅) | 앙상블 로직 구현 | |
| **Day 5** | E2E 파이프라인 테스트 | 시점기반 백테스트 실행 | 앙상블 `predict_game()` 동작 |
| | 크롤링 안정성 테스트 (1일 자동 실행) | Calibration 적용 | 백엔드 파트에 prediction_service 전달 |
| | 문서화 | 모델 아티팩트 생성 (.pkl, .pt) | 아티팩트 파일 3개 존재 |

---

## 5. 배포 가이드

### ML 모델 파일 관리

모델 파일(`.pkl`, `.pt`)은 용량이 커서 Git에 올릴 수 없습니다. 배포 시 별도로 서버에 복사합니다.

```bash
# 로컬 → EC2로 모델 파일 전송
scp -i your-key.pem \
  backend/app/ml/artifacts/kbo_xgb_v1.pkl \
  ubuntu@EC2_IP:~/kbo-predict/backend/app/ml/artifacts/

scp -i your-key.pem \
  backend/app/ml/artifacts/kbo_lstm_v1.pt \
  ubuntu@EC2_IP:~/kbo-predict/backend/app/ml/artifacts/

scp -i your-key.pem \
  backend/app/ml/artifacts/calibrator.pkl \
  ubuntu@EC2_IP:~/kbo-predict/backend/app/ml/artifacts/
```

### 크롤링 첫 실행 (학습 데이터 수집)

EC2 서버에서 최초 1회 실행:

```bash
# Docker 실행 상태에서
cd kbo-predict/backend
source venv/bin/activate

# 과거 데이터 일괄 수집 (3시즌 — 수 시간 소요)
python -c "
from app.db.database import SessionLocal
from app.crawler.pipeline import run_bulk_historical_collection
db = SessionLocal()
run_bulk_historical_collection('20230101', '20251212', db)
db.close()
"
```

### 모델 재학습 스케줄

```bash
# backend/app/scheduler/tasks.py에 추가
# 매주 일요일 새벽 3시 재학습
@scheduler.scheduled_job('cron', day_of_week='sun', hour=3)
def weekly_retrain():
    logger.info("🔄 주간 모델 재학습 시작")
    # python -m app.ml.xgboost_model 실행
```

---

## 6. 최종 체크리스트

### A팀 (크롤링) 체크리스트

- [ ] `base_crawler.py` — 딜레이, 재시도, UA 로테이션 동작 확인
- [ ] `kbo_official_crawler.py` — `fetch_team_rank_daily()` 실제 데이터 반환 확인
- [ ] `team_daily_snapshots` — 3시즌 날짜별 스냅샷 적재 완료
- [ ] `statiz_crawler.py` — 로그인 성공, 투수 시즌 통계 수집 확인
- [ ] `player_season_stats` — 선발 투수 20명 이상 통계 저장
- [ ] `naver_crawler.py` — 당일 선발 투수 정상 수집 확인
- [ ] `pipeline.py` — `run_morning_pipeline()` / `run_evening_pipeline()` 에러 없이 실행
- [ ] `crawl_logs` — 크롤링 이력 정상 기록
- [ ] `data/cache/player_ids.json` — Statiz player_no 캐시 파일 생성
- [ ] `.gitignore` — `data/`, `*.pkl`, `*.pt` Git 미포함 확인

### B팀 (ML/DL) 체크리스트

- [ ] `feature_engineering.py` — `build_features_for_game()` 1경기 테스트 성공
- [ ] `feature_engineering.py` — `as_of_date` 미래 데이터 누출 없음 (수동 검증)
- [ ] `build_training_data.py` — `training_set.parquet` 생성 완료
- [ ] 학습 데이터 홈팀 승률 0.45~0.55 범위 (데이터 편향 없음)
- [ ] `xgboost_model.py` — Test Accuracy ≥ 55% 달성
- [ ] `xgboost_model.py` — LogLoss ≤ 0.69 달성
- [ ] `artifacts/kbo_xgb_v1.pkl` — 모델 저장 확인
- [ ] `artifacts/calibrator.pkl` — Calibrator 저장 확인
- [ ] `backtest.py` — 시점기반 백테스트 정확도 55~62% (65% 초과 시 look-ahead bias 의심)
- [ ] `pytorch_model.py` — LSTM 모델 학습 성공 (or 시간 부족 시 XGBoost만으로 출시)
- [ ] `artifacts/kbo_lstm_v1.pt` — LSTM 모델 저장 확인
- [ ] `ensemble.py` — `ensemble_prediction()` 함수 단위 테스트 통과
- [ ] `prediction_service.py` — `predict_game(game_id, db)` 백엔드 연동 확인
- [ ] 선발 미확정 경기 → `confidence_level='LOW'` 정상 처리 확인
- [ ] Claude API 연동 → 예측 근거 텍스트 생성 확인

### 리스크 대응 체크

| 리스크 | 대응 |
|--------|------|
| Statiz IP 차단 | 딜레이를 3초로 늘리고 다음 날 시도 |
| 3시즌 수집 지연 | 2시즌(2024, 2025)으로 줄여 학습 시작 |
| LSTM이 XGBoost보다 나쁨 | 앙상블 가중치 XGBoost 0.9, LSTM 0.1로 설정 |
| 백테스트 65% 초과 | `as_of_date` 적용 여부 재검토, 시즌 누적값 확인 |
| 시즌 초 데이터 부족 | 전 시즌 통계를 prior로 사용, confidence_level='LOW' |

---

> 📌 **백엔드 & 프론트엔드 파트 가이드라인은 별도 문서(`KBO_백엔드_프론트엔드_가이드라인.md`)를 참고하세요.**  
> 💬 **막히는 부분은 즉시 팀 채널에 공유하세요. 특히 Statiz 파싱 오류나 DB 연결 문제는 같이 해결합시다!**
