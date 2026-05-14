# ⚾ KBO 야구 승부예측 AI — 데이터 & ML/DL 상세 설계

> **본 문서의 범위**: 데이터 크롤링/마이닝 + ML(XGBoost) + DL(PyTorch) 파이프라인
> **전제**: 백엔드(FastAPI) / 프론트엔드(Next.js) / DB 스키마는 기존 설계 문서 v1.0 그대로 유지
> **참고 레퍼런스**:
> - `limanho001014-create/kbo-predictor-dynamic` — XGBoost v3 모델(검증셋 58.6%), 35개 피처
> - `ldh-mini/baseball-sim` — Statiz 크롤러 + 베이지안 3-Layer 블렌딩(백테스트 75%, 시점예측 68%)
>
> **팀 분담** (이미지 기준): A=데이터, B=ML/DL, C=백엔드/서비스 → 본 문서는 **A·B의 작업 전부**를 다룸

---

## 목차

- [PART 1. 데이터 수집(크롤링) 아키텍처](#part-1-데이터-수집크롤링-아키텍처)
- [PART 2. 크롤러별 상세 구현](#part-2-크롤러별-상세-구현)
- [PART 3. 데이터 마이닝 & 피처 엔지니어링](#part-3-데이터-마이닝--피처-엔지니어링)
- [PART 4. Stage 1 — XGBoost 모델 설계](#part-4-stage-1--xgboost-모델-설계)
- [PART 5. Stage 2 — PyTorch DL 모델 설계](#part-5-stage-2--pytorch-dl-모델-설계)
- [PART 6. 앙상블 & 모델 서빙](#part-6-앙상블--모델-서빙)
- [PART 7. 진행 순서 & 7일 실행 가이드](#part-7-진행-순서--7일-실행-가이드)

---

# PART 1. 데이터 수집(크롤링) 아키텍처

## 1-1. 데이터 소스 선정 — 왜 이걸 쓰는가

| 소스 | 데이터 종류 | 인증 | 우선순위 | 비고 |
|------|------------|------|---------|------|
| **Statiz (statiz.co.kr)** | 선수 시즌 스탯, 최근 N경기, WAR/FIP/WHIP 등 세이버메트릭스 | **로그인 필요** | P0 | 가장 풍부한 데이터, baseball-sim에서 이미 사용 중 |
| **KBO 공식 (koreabaseball.com)** | 팀 순위, 최근 10경기, 연승/연패, 일정 | 없음 | P0 | TeamRankDaily — 과거 임의 날짜 조회 가능 (시점기반 백테스트의 핵심) |
| **네이버 스포츠 (sports.naver.com)** | 당일 선발 투수, 라인업, 경기 결과 | 없음 | P0 | 선발 투수 확정 정보는 여기가 가장 빠름 |
| **기상청 API** | 경기 당일 날씨 (강수확률, 풍속, 기온) | API 키 | P1 | 야외 구장 영향, 옥내 경기는 무시 가능 |
| **Odds API** | 배당률 | API 키 (유료/무료 제한) | P2 | ROI 검증용, MVP 단계에선 선택 |

**핵심 결정**: 두 저장소 모두 Statiz를 사용하므로 **Statiz를 메인 소스로 통합**하되, 팀 단위 시계열(최근 폼)은 **KBO 공식의 TeamRankDaily**가 더 신뢰도 높음(과거 임의 날짜 스냅샷 가능).

## 1-2. 크롤링 디렉토리 구조

기존 설계 문서의 `backend/app/crawler/` 구조를 그대로 따르되, 책임을 명확히 분리합니다.

```
backend/app/crawler/
├── __init__.py
├── base_crawler.py           # 공통: 세션, 재시도, 딜레이, User-Agent 로테이션
├── statiz_crawler.py         # 선수 스탯 (로그인 + p_no 매핑)
├── kbo_official_crawler.py   # 팀 순위 / TeamRankDaily (시점 백테스트용)
├── naver_crawler.py          # 선발 투수, 일정
├── weather_client.py         # 기상청 API
├── odds_client.py            # 배당률 API
├── roster.py                 # 팀별 로스터 (baseball-sim의 ROSTER 참고)
└── pipeline.py               # 통합 실행기 (스케줄러에서 호출)
```

## 1-3. base_crawler.py — 모든 크롤러의 기반

baseball-sim의 `statiz_crawler.py`에 있는 `safe_get` 패턴이 가장 안정적이었습니다. 이를 일반화합니다.

```python
# backend/app/crawler/base_crawler.py
import time, random, logging
import requests
from typing import Optional

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 ...",
    # 3~5개 로테이션
]

class BaseCrawler:
    def __init__(self, delay: float = 2.0, max_retries: int = 3, retry_wait: int = 30):
        self.delay = delay
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.session = requests.Session()
        self._rotate_ua()

    def _rotate_ua(self):
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        })

    def safe_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """403/429 시 백오프 재시도. 매 호출 후 self.delay 만큼 sleep."""
        for attempt in range(self.max_retries):
            resp = self.session.get(url, **kwargs)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                time.sleep(self.delay + random.uniform(0, 0.5))  # 지터
                return resp
            if resp.status_code in (403, 429):
                wait = self.retry_wait * (attempt + 1)
                logging.warning(f"[{resp.status_code}] {wait}s 대기 후 재시도 ({attempt+1}/{self.max_retries})")
                self._rotate_ua()
                time.sleep(wait)
                continue
            resp.raise_for_status()
        return None
```

**핵심 원칙**:
- 요청 간 2초 + 지터(0~0.5초): 봇 탐지 회피
- 403/429 시 30 → 60 → 90초 백오프 + UA 로테이션
- 모든 크롤링 호출 결과를 **`crawl_logs` 테이블에 기록**(이미 설계문서에 있음) — 실패율 모니터링용

## 1-4. 스케줄링 & 실행 시점

설계 문서의 APScheduler 기본 구조를 유지하되, **시점 정확도 보장**을 위해 단계 분리:

```
매일 06:00  → kbo_official_crawler: 어제 경기 결과 + 팀 순위 갱신
              statiz_crawler: 선수 시즌 통계 갱신 (변동분만)
              → 결과는 games / team_game_stats / pitcher_game_stats / player_season_stats 테이블

매일 18:00  → naver_crawler: 당일 선발 투수 확정 정보
              weather_client: 경기 당일 날씨
              → game_predictions 테이블에 1차 예측(선발 미확정분)을 LOW confidence로 기록

매일 19:30  → ML 추론 트리거: Stage1+Stage2 앙상블 실행
              Claude API: 근거 생성
              → game_predictions 테이블에 최종본 is_final=True 기록
              → Redis 캐시 invalidate
```

baseball-sim의 `npm run predict` 한 줄 파이프라인 컨셉이 매우 깔끔했습니다. 본 프로젝트에서는 **`pipeline.py`의 `run_daily_pipeline()`** 단일 함수로 통합합니다.

---

# PART 2. 크롤러별 상세 구현

## 2-1. Statiz 크롤러 (선수 스탯)

baseball-sim의 `statiz_crawler.py`를 거의 그대로 활용합니다. **다만 다음을 수정**:

### 수정 포인트

1. **하드코딩된 자격증명 제거** → `.env`의 `STATIZ_USER`, `STATIZ_PASS`
2. **JSON 파일 출력 → DB INSERT/UPSERT**로 변경
3. **`player_ids.json`은 캐시로 유지** (검색 비용 절감)
4. **`is_foreign` 자동 판단**: ROSTER에 외국인 표시 추가

### 데이터 흐름

```
[로그인] → [player_ids.json 캐시 확인] → [없으면 search_player()] → [player_url 크롤링]
   → [parse_season_table()] → [extract_batter_stats / extract_pitcher_stats]
   → [DB UPSERT: players + player_season_stats]
```

### 추가로 크롤링할 페이지

| URL 패턴 | 추출 내용 | 용도 |
|---------|----------|------|
| `/player/?m=playerinfo&p_no={}&so=ALL` | 시즌별 전체 기록 | 학습 데이터 (3시즌) |
| `/player/?m=playerinfo&p_no={}&opt=4` | 최근 5경기 game log | 단기 폼 피처 |
| `/player/?m=playerinfo&p_no={}&opt=3` | 상대 팀별 성적 | H2H 피처 |
| `/stat/team/?m=team` | 팀 합산 OPS/ERA | team_season_stats |

### 신규 테이블 추가 권장

기존 DB 스키마에는 **시즌 누적 통계 테이블이 없습니다**. 사건형(game_stats)만 있어서 매번 집계 쿼리를 돌려야 하므로 다음 테이블을 추가합니다:

```sql
CREATE TABLE player_season_stats (
  id              SERIAL PRIMARY KEY,
  player_id       INT NOT NULL REFERENCES players(id),
  season          SMALLINT NOT NULL,
  -- 타자
  avg             DECIMAL(4,3),
  obp             DECIMAL(4,3),
  slg             DECIMAL(4,3),
  ops             DECIMAL(5,3),
  hr              SMALLINT,
  rbi             SMALLINT,
  sb              SMALLINT,
  war_batter      DECIMAL(4,2),
  -- 투수
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

CREATE TABLE team_season_stats (
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

## 2-2. KBO 공식 크롤러 (팀 시계열)

**baseball-sim의 가장 강력한 부분이 이 크롤러**입니다. 이유:

- KBO 공식 TeamRankDaily 페이지는 **과거 임의 날짜의 팀 순위·최근 10경기·연승/연패 스냅샷**을 제공
- 이걸로 **look-ahead bias 없는 시점기반 백테스트**가 가능 (모델 학습할 때 결정적으로 중요)

### URL 패턴

```
https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx?seriesId=0&date={YYYYMMDD}
```

`date` 파라미터를 바꾸면 그 시점의 순위 스냅샷을 받음.

### 구현 (단순 cheerio/BS4)

```python
# backend/app/crawler/kbo_official_crawler.py
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler

class KBOOfficialCrawler(BaseCrawler):
    BASE = "https://www.koreabaseball.com"
    
    def fetch_team_rank_daily(self, date: str) -> list[dict]:
        """date: 'YYYYMMDD' — 해당 시점의 팀 순위 스냅샷"""
        url = f"{self.BASE}/Record/TeamRank/TeamRankDaily.aspx?seriesId=0&date={date}"
        resp = self.safe_get(url)
        if not resp: return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.tData")  # 실제 셀렉터는 확인 필요
        rows = []
        for tr in table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            # 컬럼: 순위 | 팀 | 경기 | 승 | 패 | 무 | 승률 | 게임차 | 최근10경기 | 연속
            rows.append({
                "rank": int(cells[0]),
                "team": cells[1],
                "games": int(cells[2]),
                "wins": int(cells[3]),
                "losses": int(cells[4]),
                "draws": int(cells[5]),
                "win_rate": float(cells[6]),
                "last_10": cells[8],          # 예: "7승 3패"
                "streak": cells[9],            # 예: "3연승"
            })
        return rows
    
    def fetch_schedule(self, year: int, month: int) -> list[dict]:
        """월별 일정"""
        url = f"{self.BASE}/Schedule/Schedule.aspx?seriesId=0&gameMonth={month}&seasonId={year}"
        # ... 파싱
```

### 일별 스냅샷 저장 (시점 백테스트의 핵심)

baseball-sim의 `team-stats-snapshots/` 폴더 컨셉을 그대로 도입합니다. **모든 일자별 팀 통계를 별도 테이블에 저장**해서, 학습 시 "그 경기 시점에 알 수 있었던 정보만" 사용 가능하게 만듭니다:

```sql
CREATE TABLE team_daily_snapshots (
  id              SERIAL PRIMARY KEY,
  team_id         INT NOT NULL REFERENCES teams(id),
  snapshot_date   DATE NOT NULL,             -- 이 날짜 기준 누적값
  rank            SMALLINT,
  games_played    SMALLINT,
  wins            SMALLINT,
  losses          SMALLINT,
  draws           SMALLINT,
  season_win_rate DECIMAL(4,3),
  last10_wins     SMALLINT,
  last10_losses   SMALLINT,
  streak_type     VARCHAR(10),               -- 'WIN' | 'LOSS' | 'DRAW'
  streak_count    SMALLINT,
  created_at      TIMESTAMP DEFAULT NOW(),
  UNIQUE(team_id, snapshot_date)
);
CREATE INDEX idx_team_snapshots_date ON team_daily_snapshots(snapshot_date);
```

**이게 왜 중요한가**: 학습 데이터에 "그 시점에 알 수 없던 미래 정보(season_win_rate가 미래 경기까지 반영된 값)"가 섞이면 백테스트 성능이 비현실적으로 부풀려집니다. baseball-sim 팀이 v9.3에서 모멘텀 +8%p를 검증할 수 있었던 게 이 스냅샷 구조 덕분.

## 2-3. 네이버 스포츠 크롤러 (선발 투수)

선발 투수는 보통 **경기 전날 저녁~당일 오전**에 확정됩니다.

### URL 패턴

```
https://sports.news.naver.com/kbaseball/schedule/index.nhn?date={YYYY-MM-DD}
```

각 경기 카드를 클릭하면 미리보기 페이지(`gameId` 포함)가 나오고, 거기에 선발 투수가 표시됩니다.

```
https://sports.news.naver.com/game/index.nhn?gameId={gameId}
```

### 구현 포인트

- **선발 미확정 시 `home_starter_id=NULL`로 저장**, `confidence_level='LOW'`로 1차 예측만 게시
- 18시 크롤링 이후에도 NULL이면 19:30 추론 시 **팀 통계 기반으로만 예측**
- DOM 구조가 SPA라면 Playwright로 전환 필요 (baseball-sim도 v9.3에서 백필용으로 Playwright 사용함)

## 2-4. 기상청 / 배당률 API

**기상청 API**: 단기예보 조회서비스 (`getVilageFcst`) — 구장 위치(위/경도)로 조회

```python
# backend/app/crawler/weather_client.py
async def fetch_weather(stadium: str, game_datetime: datetime) -> dict:
    # 잠실 위경도: 37.5126, 127.0719 등 hardcode
    # 강수확률(POP), 풍속(WSD), 기온(T1H) 등 추출
    return {"pop": 30, "wind_speed": 2.5, "temp": 18.0, "is_rain_risk": False}
```

**Odds API**: MVP는 생략해도 무방. v1.1에서 ROI 시뮬레이션 추가 시 도입.

---

# PART 3. 데이터 마이닝 & 피처 엔지니어링

## 3-1. 피처 카탈로그 (35개)

`kbo_predictor-dynamic`의 v3 모델 피처를 그대로 베이스라인으로 사용하되, 본 프로젝트의 데이터 가용성에 맞춰 분류합니다.

### 그룹 1 — 팀 누적 통계 (시즌 + 최근 10경기)

| 피처명 | 계산식 | 소스 |
|--------|--------|------|
| `home_season_win_rate` | 시즌 승 / (승+패) | team_daily_snapshots |
| `away_season_win_rate` | " | " |
| `home_last10_win_rate` | 최근 10경기 승률 | team_daily_snapshots.last10_wins / 10 |
| `away_last10_win_rate` | " | " |
| `home_home_win_rate` | 홈 경기만 승률 (시즌 누적) | games + team_game_stats 집계 |
| `away_away_win_rate` | 원정 경기만 승률 | " |
| `home_streak`, `away_streak` | 연승/연패 (음수=연패) | team_daily_snapshots.streak_count × 부호 |

### 그룹 2 — 팀 타격/투구 능력치

| 피처명 | 계산식 | 소스 |
|--------|--------|------|
| `home_ops`, `away_ops` | 팀 시즌 OPS | team_season_stats |
| `home_era`, `away_era` | 팀 시즌 ERA | " |
| `home_run_diff_last10` | 최근 10경기 평균 득점 - 평균 실점 | team_game_stats 집계 |
| `away_run_diff_last10` | " | " |

### 그룹 3 — 선발 투수 (가장 중요한 그룹)

| 피처명 | 계산식 | 소스 |
|--------|--------|------|
| `home_starter_era` | 선발 시즌 ERA | player_season_stats |
| `away_starter_era` | " | " |
| `home_starter_recent5_era` | 최근 5경기 ERA | pitcher_game_stats 집계 |
| `away_starter_recent5_era` | " | " |
| `home_starter_whip`, `away_starter_whip` | 시즌 WHIP | player_season_stats |
| `home_ace_era`, `away_ace_era` | 팀 1선발 ERA | players(role='ACE') 또는 ROSTER 정의 |

### 그룹 4 — 불펜 & 타선 깊이

| 피처명 | 계산식 |
|--------|--------|
| `home_bullpen_era`, `away_bullpen_era` | 선발 제외 투수들의 ERA 가중평균 |
| `home_pitcher_depth`, `away_pitcher_depth` | ERA<5.0 투수 수 |
| `home_top5_ops`, `away_top5_ops` | 타석 많은 상위 5명의 OPS 평균 |
| `home_hr_power`, `away_hr_power` | 팀 시즌 홈런 수 |
| `home_hitter_depth`, `away_hitter_depth` | OPS>0.7 타자 수 |

### 그룹 5 — H2H & 컨텍스트

| 피처명 | 계산식 |
|--------|--------|
| `h2h_home_win_rate` | 최근 3시즌 두 팀 맞대결에서 홈팀 승률 |
| `rest_diff` | (홈팀 휴식일) - (원정팀 휴식일) |
| `is_weekend` | 토/일 = 1 |
| `is_dome` | 돔구장 = 1 (날씨 영향 제거) |

### 그룹 6 — 차이값 피처 (Diff features)

v3 모델에서 14개의 diff 피처가 강력했습니다. 두 팀 값의 차이를 명시적으로 주면 모델이 "상대 우위"를 직접 학습합니다.

```python
era_diff = away_era - home_era       # 클수록 홈팀 우세
ops_diff = home_ops - away_ops
last10_wr_diff = home_last10_wr - away_last10_wr
season_wr_diff = ...
starter_era_diff = away_starter_era - home_starter_era
# ... 등 14개
```

### 그룹 7 — 날씨 (선택)

`weather_pop`, `weather_wind_speed`, `weather_is_rain` — 야외 구장에만 적용

**합계**: 33 + 차이 14 = **47개 피처** (v3의 35개를 확장)

## 3-2. 피처 계산 파이프라인

```
backend/app/ml/feature_engineering.py
```

핵심 함수 시그니처:

```python
def build_features_for_game(
    game_id: int,
    *,
    as_of_date: date = None,  # ★ 시점 백테스트용: 이 날짜까지의 정보만 사용
    db: Session
) -> pd.DataFrame:
    """단일 경기에 대해 피처 1행 생성.
    
    핵심: as_of_date를 받아서 그 시점에 알 수 있었던 정보만 사용.
    학습 시 → as_of_date = (경기일 - 1일)
    추론 시 → as_of_date = None (현재 시점)
    """
    game = db.query(Game).get(game_id)
    cutoff = as_of_date or (game.scheduled_at.date() - timedelta(days=1))
    
    home_snapshot = get_team_snapshot(game.home_team_id, cutoff, db)
    away_snapshot = get_team_snapshot(game.away_team_id, cutoff, db)
    
    home_starter_stats = get_pitcher_recent_stats(
        game.game_predictions[-1].home_starter_id, cutoff, db
    )
    # ... 모든 피처 계산
    
    return pd.DataFrame([{
        "home_season_win_rate": home_snapshot.season_win_rate,
        "home_last10_win_rate": home_snapshot.last10_wins / 10,
        # ... 47개
    }])
```

**왜 `as_of_date`가 중요한가**: 학습 데이터셋을 만들 때 "2024년 5월 1일 경기"에 대한 피처를 계산하면서 실수로 2024년 5월~10월 데이터를 다 합쳐버리면(시즌 누적값), 모델은 미래를 보고 학습하는 셈이 됩니다. 백테스트는 75%인데 실전은 50%인 전형적인 함정. baseball-sim이 v9.3에서 처음으로 진짜 시점 예측 68%를 측정할 수 있었던 이유가 바로 이 분리 때문입니다.

## 3-3. 학습 데이터셋 빌드 스크립트

```python
# backend/app/ml/build_training_data.py
def build_training_dataset(
    seasons: list[int] = [2023, 2024, 2025],
    output_path: str = "data/training_set.parquet"
):
    """모든 완료 경기에 대해 피처 + 정답(홈승=1, 원정승=0) 생성."""
    rows = []
    games = db.query(Game).filter(
        Game.season.in_(seasons),
        Game.status == "COMPLETED"
    ).all()
    
    for game in tqdm(games):
        as_of = game.scheduled_at.date() - timedelta(days=1)
        features = build_features_for_game(game.id, as_of_date=as_of, db=db)
        features["label"] = 1 if game.home_score > game.away_score else 0
        features["game_id"] = game.id
        features["scheduled_at"] = game.scheduled_at
        rows.append(features)
    
    df = pd.concat(rows, ignore_index=True)
    df.to_parquet(output_path)
    return df
```

**예상 데이터량**: KBO 정규시즌 ≈ 720경기/시즌 × 3시즌 = **약 2,160개 학습 샘플** × 47 피처

---

# PART 4. Stage 1 — XGBoost 모델 설계

## 4-1. 왜 XGBoost인가 (Tabular 데이터의 정답)

- 47개 정형 피처에 대해 트리 앙상블이 신경망보다 안정적
- 결측치 자동 처리 (선발 투수 미확정 등)
- 학습 빠름 (수 분 내), 해석 가능 (feature_importances_)
- v3 모델이 이미 검증셋 58.6%를 찍음 → **그대로 베이스라인**

## 4-2. 학습 파이프라인

```
backend/app/ml/xgboost_model.py
```

### Train/Val/Test 분할 — 시간순!

**❌ 절대 금지**: `train_test_split(shuffle=True)` — look-ahead bias
**✅ 정답**: 시간 기준 분할

```python
df = df.sort_values("scheduled_at")
n = len(df)
train = df.iloc[:int(n*0.7)]          # 2023 전부 + 2024 일부
val   = df.iloc[int(n*0.7):int(n*0.85)]  # 2024 후반
test  = df.iloc[int(n*0.85):]           # 2025 (실전과 가장 유사)
```

### 모델 정의 & 학습

```python
import xgboost as xgb

FEATURES = [...]  # 47개 피처명

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
    tree_method="hist",  # 빠름
)

model.fit(
    train[FEATURES], train["label"],
    eval_set=[(val[FEATURES], val["label"])],
    verbose=50
)
```

### 평가 지표

```python
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.calibration import calibration_curve

pred_proba = model.predict_proba(test[FEATURES])[:, 1]
pred = (pred_proba > 0.5).astype(int)

print(f"Accuracy: {accuracy_score(test['label'], pred):.4f}")
print(f"LogLoss:  {log_loss(test['label'], pred_proba):.4f}")
print(f"Brier:    {brier_score_loss(test['label'], pred_proba):.4f}")
# ECE (Expected Calibration Error)도 계산
```

**목표**:
- MVP: Accuracy ≥ 55%, LogLoss ≤ 0.69
- 최종: Accuracy ≥ 58%, LogLoss ≤ 0.65, ECE ≤ 0.05

## 4-3. 하이퍼파라미터 튜닝 (Optuna)

Day 5에 시간 있으면 적용:

```python
import optuna
def objective(trial):
    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        # ...
    }
    model = xgb.XGBClassifier(**params, n_estimators=500, early_stopping_rounds=30)
    model.fit(train[FEATURES], train["label"], eval_set=[(val[FEATURES], val["label"])], verbose=False)
    return log_loss(val["label"], model.predict_proba(val[FEATURES])[:, 1])

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=50, timeout=1800)  # 30분 컷
```

## 4-4. 모델 저장 포맷 (v3 호환)

```python
import joblib
artifact = {
    "model": model,
    "features": FEATURES,
    "model_name": "xgboost_v1",
    "version": "v1.0",
    "label_map": {0: "AWAY_WIN", 1: "HOME_WIN"},
    "needs_scale": False,
    "scaler": None,
    "trained_at": datetime.now().isoformat(),
    "test_accuracy": float(test_acc),
    "test_logloss": float(test_logloss),
}
joblib.dump(artifact, "backend/app/ml/artifacts/kbo_xgb_v1.pkl")
```

이 포맷은 `kbo-predictor-dynamic`의 `kbo_predictor.py`와 100% 호환됩니다. → 서빙 코드 재사용 가능.

## 4-5. 시점기반 백테스팅 (검증의 핵심)

baseball-sim에서 가장 인상적이었던 부분. 단순히 test set 정확도가 아니라, **"매일 그날까지의 정보만으로 그날 경기를 예측"** 하는 시뮬레이션을 돌립니다.

```python
def time_based_backtest(
    start_date: date,
    end_date: date,
    model_artifact_path: str
) -> dict:
    """시점기반 백테스트.
    각 날짜에 대해, 그 날짜의 D-1 시점 피처로 D일 경기 예측 → 실제 결과와 비교.
    """
    artifact = joblib.load(model_artifact_path)
    model = artifact["model"]
    features = artifact["features"]
    
    results = []
    for d in daterange(start_date, end_date):
        games = db.query(Game).filter(
            func.date(Game.scheduled_at) == d,
            Game.status == "COMPLETED"
        ).all()
        for g in games:
            X = build_features_for_game(g.id, as_of_date=d - timedelta(days=1), db=db)
            pred_proba = model.predict_proba(X[features])[0, 1]
            actual = 1 if g.home_score > g.away_score else 0
            results.append({
                "date": d, "game_id": g.id,
                "predicted_home_prob": pred_proba,
                "predicted": int(pred_proba > 0.5),
                "actual": actual,
                "correct": int(pred_proba > 0.5) == actual,
                "confidence": "HIGH" if abs(pred_proba - 0.5) > 0.15 else
                              "MEDIUM" if abs(pred_proba - 0.5) > 0.08 else "LOW",
            })
    
    df = pd.DataFrame(results)
    return {
        "overall_accuracy": df["correct"].mean(),
        "high_conf_accuracy": df[df["confidence"] == "HIGH"]["correct"].mean(),
        "medium_conf_accuracy": df[df["confidence"] == "MEDIUM"]["correct"].mean(),
        "low_conf_accuracy": df[df["confidence"] == "LOW"]["correct"].mean(),
        "total_games": len(df),
    }
```

---

# PART 5. Stage 2 — PyTorch DL 모델 설계

## 5-1. 왜 DL을 추가하는가 (현실적인 판단)

XGBoost가 이미 58.6%인데 DL을 더하는 게 의미가 있을까? **솔직히 야구는 분산이 크기 때문에 60% 넘기기가 어렵습니다**. 그래도 DL을 추가하는 이유:

1. **시계열 정보**: 선발 투수의 최근 5경기 추이는 평균(ERA)만으로는 부족 (1.5 → 2.5 → 4.0 의 악화 추세 vs 4.0 → 2.5 → 1.5의 회복 추세)
2. **포트폴리오**: 캡스톤/MVP 관점에서 "ML+DL 둘 다 했다"가 중요
3. **앙상블 효과**: 모델 다양성으로 logloss 개선 가능 (Accuracy는 +1~2%p 정도 기대)

**현실 체크**: Day 3 내 완성 안 되면 **XGBoost 단독으로 출시**하고 v1.1에서 추가 (이미지의 병목 리스크 명시대로).

## 5-2. 모델 선택: TabTransformer vs LSTM

| 모델 | 장점 | 단점 | 권장 |
|------|------|------|------|
| **TabTransformer** | 카테고리 변수 임베딩, 피처 간 어텐션 | 학습 데이터 적으면 과적합 | 2,160 샘플엔 부담 |
| **LSTM (단기 시퀀스)** | 선발 투수 최근 5경기 같은 시계열 처리 직관적 | 카테고리 변수 처리 부담 | **권장** |
| **하이브리드 (LSTM + MLP)** | LSTM이 시계열 부분, MLP가 정적 부분 | 구현 복잡도 ↑ | 시간 되면 시도 |

**최종 선택**: **LSTM + MLP 하이브리드** (Day 6~7에 구현)

## 5-3. LSTM + MLP 하이브리드 아키텍처

### 입력 구성

```
시계열 입력 (LSTM 처리):
  - 홈 선발 최근 5경기: shape (5, 5) — [ERA, WHIP, K, IP, ER]
  - 원정 선발 최근 5경기: shape (5, 5)
  - 홈팀 최근 10경기: shape (10, 4) — [득점, 실점, 승패, 홈여부]
  - 원정팀 최근 10경기: shape (10, 4)

정적 입력 (MLP 처리):
  - 그룹 1~6의 누적 피처 47개 중 시계열로 표현 안 된 것들 약 30개
```

### 모델 정의

```python
import torch
import torch.nn as nn

class KBOPredictionModel(nn.Module):
    def __init__(
        self,
        pitcher_seq_len: int = 5, pitcher_feat_dim: int = 5,
        team_seq_len: int = 10, team_feat_dim: int = 4,
        static_dim: int = 30,
        hidden: int = 64,
    ):
        super().__init__()
        # 선발 투수 LSTM (홈/원정 공유)
        self.pitcher_lstm = nn.LSTM(
            input_size=pitcher_feat_dim,
            hidden_size=hidden,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
        )
        # 팀 폼 LSTM
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
            nn.Dropout(0.3),
        )
        # 결합 후 출력
        self.head = nn.Sequential(
            nn.Linear(hidden * 5, hidden),  # 홈투수+원정투수+홈팀+원정팀+정적
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden, 1),
        )
    
    def forward(self, home_p, away_p, home_t, away_t, static):
        _, (h_hp, _) = self.pitcher_lstm(home_p)
        _, (h_ap, _) = self.pitcher_lstm(away_p)
        _, (h_ht, _) = self.team_lstm(home_t)
        _, (h_at, _) = self.team_lstm(away_t)
        h_st = self.static_mlp(static)
        
        combined = torch.cat([
            h_hp.squeeze(0), h_ap.squeeze(0),
            h_ht.squeeze(0), h_at.squeeze(0), h_st
        ], dim=1)
        logit = self.head(combined)
        return torch.sigmoid(logit).squeeze(-1)
```

### 학습 루프

```python
import torch.optim as optim
from torch.utils.data import DataLoader

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = KBOPredictionModel().to(device)
optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)
criterion = nn.BCELoss()

best_val_loss = float("inf")
patience = 10
patience_counter = 0

for epoch in range(50):
    model.train()
    for batch in train_loader:
        # batch: dict with home_p, away_p, home_t, away_t, static, label
        optimizer.zero_grad()
        pred = model(**{k: v.to(device) for k, v in batch.items() if k != "label"})
        loss = criterion(pred, batch["label"].float().to(device))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
    
    # validation
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch in val_loader:
            pred = model(**{k: v.to(device) for k, v in batch.items() if k != "label"})
            val_loss += criterion(pred, batch["label"].float().to(device)).item()
    val_loss /= len(val_loader)
    
    scheduler.step()
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "kbo_lstm_v1.pt")
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch}")
            break
```

## 5-4. HuggingFace 사전학습 활용 (선택)

기획서에 "TimesFM, TinyTimeMixer Fine-tuning" 언급이 있는데, 2,160개 샘플로는 사전학습 모델을 효과적으로 fine-tune하기 어려울 수 있습니다.

**현실적 접근**:
- MVP에선 **위의 LSTM 처음부터 학습**
- v1.1에서 TimesFM의 임베딩만 추출 → MLP 헤드 학습 (얕은 fine-tuning)

## 5-5. 모델 저장

```python
artifact = {
    "model_state_dict": model.state_dict(),
    "model_config": {...},
    "feature_spec": {
        "pitcher_seq_len": 5,
        "team_seq_len": 10,
        "static_features": [...],
    },
    "version": "v1.0-lstm",
    "test_accuracy": ...,
}
torch.save(artifact, "backend/app/ml/artifacts/kbo_lstm_v1.pt")
```

---

# PART 6. 앙상블 & 모델 서빙

## 6-1. 앙상블 전략 — 베이지안 블렌딩

baseball-sim의 v9.4가 도달한 가장 정교한 부분. 단순 가중평균(`0.6 * xgb + 0.4 * lstm`)도 OK지만, 더 좋은 방법:

### 신뢰도 기반 동적 가중

```python
def ensemble_prediction(xgb_proba: float, lstm_proba: float, context: dict) -> dict:
    """
    XGBoost와 LSTM이 일치하면 신뢰도 ↑, 불일치하면 보수적으로.
    """
    # 기본 가중치
    w_xgb = 0.6
    w_lstm = 0.4
    
    # 두 모델 차이가 크면 LSTM 가중치 감소 (LSTM이 outlier일 가능성)
    diff = abs(xgb_proba - lstm_proba)
    if diff > 0.20:
        w_xgb = 0.75
        w_lstm = 0.25
    
    # 선발 미확정 시 정적 피처만 신뢰
    if context.get("starter_unconfirmed"):
        w_xgb = 1.0
        w_lstm = 0.0
    
    final = w_xgb * xgb_proba + w_lstm * lstm_proba
    
    # 신뢰도 산정
    distance_from_50 = abs(final - 0.5)
    agreement = 1.0 - diff  # 두 모델 일치도
    confidence_score = distance_from_50 * agreement
    
    if confidence_score > 0.12:
        confidence = "HIGH"
    elif confidence_score > 0.06:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "home_win_prob": final,
        "away_win_prob": 1.0 - final,
        "xgboost_home_prob": xgb_proba,
        "lstm_home_prob": lstm_proba,
        "confidence_level": confidence,
        "weights": {"xgb": w_xgb, "lstm": w_lstm},
    }
```

## 6-2. Calibration (확률 보정)

원래 모델 출력 0.7은 "70% 확신"이지만, 실제로 그 확률에서 홈팀이 65%만 이기면 과신(over-confidence)입니다. **Isotonic Regression**으로 보정합니다.

```python
from sklearn.isotonic import IsotonicRegression

# val 셋에서 학습
calibrator = IsotonicRegression(out_of_bounds="clip")
calibrator.fit(val_pred_proba, val_labels)

# 추론 시
calibrated_proba = calibrator.predict(raw_proba)
```

artifact에 같이 저장 → 서빙 시 자동 적용.

## 6-3. 추론 서비스 (PredictionService)

```python
# backend/app/services/prediction_service.py
class PredictionService:
    def __init__(self):
        self.xgb_artifact = joblib.load("backend/app/ml/artifacts/kbo_xgb_v1.pkl")
        self.lstm_model = self._load_lstm()
        self.calibrator = joblib.load("backend/app/ml/artifacts/calibrator.pkl")
    
    def predict_game(self, game_id: int, db: Session) -> GamePrediction:
        # 1. 피처 생성 (as_of_date=None → 현재 시점)
        X_tabular = build_features_for_game(game_id, db=db)
        X_sequence = build_sequence_features(game_id, db=db)
        
        # 2. Stage 1: XGBoost
        xgb_proba = self.xgb_artifact["model"].predict_proba(
            X_tabular[self.xgb_artifact["features"]]
        )[0, 1]
        xgb_proba = self.calibrator.predict([xgb_proba])[0]
        
        # 3. Stage 2: LSTM
        lstm_proba = self._lstm_predict(X_sequence)
        
        # 4. 앙상블
        context = self._build_context(game_id, db)
        result = ensemble_prediction(xgb_proba, lstm_proba, context)
        
        # 5. DB 저장
        prediction = GamePrediction(
            game_id=game_id,
            home_win_prob=result["home_win_prob"],
            away_win_prob=result["away_win_prob"],
            confidence_level=result["confidence_level"],
            xgboost_home_prob=xgb_proba,
            pytorch_home_prob=lstm_proba,
            ensemble_weight_xgb=result["weights"]["xgb"],
            model_version="v1.0-xgb+lstm",
            is_final=context["starter_confirmed"],
            predicted_at=datetime.now(),
        )
        db.add(prediction)
        db.commit()
        return prediction
```

이 함수가 C 팀원의 FastAPI 라우터(`/games/{game_id}/prediction`)에서 호출됩니다.

---

# PART 7. 진행 순서 & 7일 실행 가이드

## 7-1. A·B 팀원 일별 작업 (이미지 기준 7일 스프린트)

### Day 1 — 준비 & 데이터 수집 시작

**A (데이터)**
- 오전: `setup.sh` 실행, PostgreSQL 컨테이너 기동, 기존 DB DDL 적용
- 추가 테이블 `player_season_stats`, `team_season_stats`, `team_daily_snapshots` 생성
- `base_crawler.py` 구현
- `roster.py`에 10개 팀 로스터 정의 (baseball-sim ROSTER 복붙 + 외국인 마킹)
- 오후: `kbo_official_crawler.py` 구현, 2023~2025 시즌 일정 + 결과 수집 시작
- **완료 기준**: `games` 테이블에 3시즌 약 2,100경기 INSERT 완료

**B (ML)**
- 오전: 피처 리스트 47개 확정 (이 문서의 카탈로그 검토 후 수정)
- EDA 노트북: 기존 KBO 데이터 분포, 결측치 분석 (A가 보내주는 샘플로)
- 오후: `feature_engineering.py` 스켈레톤 작성, `as_of_date` 시그니처 합의

### Day 2 — 데이터 마무리 & XGBoost 학습

**A**
- 오전: `statiz_crawler.py` 적용 (baseball-sim 코드 → DB INSERT로 수정)
- player_ids 매핑 캐시 구축 (한 번만 돌리면 됨)
- 3시즌 선수 시즌 통계 수집
- 오후: `team_daily_snapshots` 채우기 (KBO 공식 TeamRankDaily 일자별 크롤링) — **시간 많이 걸림**, 병렬화 권장

**B**
- 오전: `build_training_dataset()` 실행 → `data/training_set.parquet` 생성
- A가 데이터 다 못 채웠으면 일부 시즌만으로 시작
- 오후: XGBoost 첫 학습 + 시간기반 split + 평가
- **완료 기준**: Test Accuracy ≥ 55%

### Day 3 — DL 시작 & 피처 개선

**A**
- 오전: `naver_crawler.py` (선발 투수) + `weather_client.py`
- 스케줄러 (`apscheduler`) 등록, 자동화 테스트
- 오후: 데이터 품질 검증, 결측치 처리 정책 정리, B 지원

**B**
- 오전: XGBoost 하이퍼파라미터 튜닝 (Optuna), 피처 중요도 분석으로 약한 피처 제거
- 오후: PyTorch LSTM 모델 코드 작성 시작
- **완료 기준**: XGBoost 정확도 58%+ OR LSTM 코드 골격 완성

### Day 4 — 통합

**A**
- 데이터 품질 최종 검증, B·C 통합 지원 (특히 추론 시점에 피처가 정상 생성되는지)

**B**
- 오전: LSTM 학습 + 시점기반 백테스트
- 오후: 앙상블 로직, calibrator 학습
- 모델 서빙 API 함수 완성 → C에게 전달
- **완료 기준**: 앙상블 + 백테스트 결과 도출, `predict_game()` 함수 동작

### Day 5 — 최종 & 버그 수정

- 전체 파이프라인 E2E 테스트
- 모델 재학습 주기 설정 (매주 일요일 새벽)
- 버그 수정, 문서화

## 7-2. 산출물 체크리스트

### A 팀원이 만들 것

- [ ] `backend/app/crawler/base_crawler.py`
- [ ] `backend/app/crawler/statiz_crawler.py`
- [ ] `backend/app/crawler/kbo_official_crawler.py`
- [ ] `backend/app/crawler/naver_crawler.py`
- [ ] `backend/app/crawler/weather_client.py`
- [ ] `backend/app/crawler/roster.py`
- [ ] `backend/app/crawler/pipeline.py`
- [ ] `backend/app/scheduler/tasks.py` (3개 cron)
- [ ] 추가 DB 마이그레이션 (`player_season_stats` 등)
- [ ] `data/cache/player_ids.json`
- [ ] DB: 3시즌 분량 데이터 적재 완료

### B 팀원이 만들 것

- [ ] `backend/app/ml/feature_engineering.py`
- [ ] `backend/app/ml/build_training_data.py`
- [ ] `backend/app/ml/xgboost_model.py`
- [ ] `backend/app/ml/pytorch_model.py`
- [ ] `backend/app/ml/ensemble.py`
- [ ] `backend/app/ml/backtest.py`
- [ ] `backend/app/ml/artifacts/kbo_xgb_v1.pkl`
- [ ] `backend/app/ml/artifacts/kbo_lstm_v1.pt`
- [ ] `backend/app/ml/artifacts/calibrator.pkl`
- [ ] `backend/app/services/prediction_service.py` (C와 공유)
- [ ] 백테스트 리포트 (`notebooks/backtest_report.ipynb`)

## 7-3. A↔B 공유 인터페이스 (이미지의 "공유 인터페이스" 부분)

```python
# 피처 컬럼명 스펙 (A→B로 전달)
FEATURE_COLUMNS = [
    "home_season_win_rate", "away_season_win_rate",
    "home_last10_win_rate", "away_last10_win_rate",
    # ... 47개, 순서 고정
]

# 시점 백테스트용 함수 시그니처 (A·B 합의)
def build_features_for_game(
    game_id: int,
    *,
    as_of_date: date = None,
    db: Session
) -> pd.DataFrame:  # shape (1, 47)
    ...

# 예측 결과 JSON 포맷 (B→C로 전달, prediction_service.py에서 반환)
{
    "home_win_prob": 0.62,
    "away_win_prob": 0.38,
    "confidence_level": "HIGH",
    "xgboost_home_prob": 0.61,
    "lstm_home_prob": 0.64,
    "model_version": "v1.0-xgb+lstm",
    "features_used": 47,
    "predicted_at": "2025-05-12T19:30:00+09:00"
}
```

## 7-4. 리스크 & 대응

| 리스크 | 시그널 | 대응 |
|--------|--------|------|
| Statiz 로그인 실패 / IP 차단 | 403 연속 발생 | 백오프 + UA 로테이션, 그래도 안되면 KBO 공식 데이터만으로 축소 |
| 3시즌 데이터 수집 늦어짐 | Day 2 종료 시점에 < 1500경기 | 2시즌(2024, 2025)으로 줄여서 일단 학습 시작 |
| LSTM 학습이 XGB보다 나쁨 | Test acc LSTM < XGB - 2%p | 앙상블에서 LSTM 가중치 0.2로 낮추거나 제외 |
| 백테스트 정확도가 비현실적으로 높음 (>65%) | look-ahead bias 의심 | `as_of_date` 누락 케이스 점검, 시즌 누적 컬럼이 미래 데이터 포함하는지 확인 |
| 신규 시즌 시작 시 데이터 부족 | 시즌 초 1~2주 | 전 시즌 데이터를 prior로 사용 (베이지안 블렌딩), `confidence_level=LOW` |

## 7-5. 코드 작성 순서 권장 (B 입장)

```
1. feature_engineering.py 스켈레톤 (시그니처만)
   ↓
2. build_training_data.py (A 데이터 일부로 동작 확인)
   ↓
3. xgboost_model.py — 최소 학습/저장/로드 사이클 완성
   ↓
4. backtest.py — 시점기반 백테스트 통과 확인 (overfit 체크)
   ↓
5. (시간 되면) pytorch_model.py
   ↓
6. ensemble.py + prediction_service.py — C와 통합
```

각 단계마다 **임시 데이터(소량)로 E2E 한번씩 돌려보고** 다음 단계로 — 마지막에 몰아서 디버깅하지 말 것.

---

## 부록 A. 핵심 파일 템플릿 위치

본 문서에서 참고/생성할 파일들:
- 베이스: `kbo-predictor-dynamic/kbo_predictor.py` (XGBoost 추론 패턴)
- 베이스: `baseball-sim/statiz_crawler.py` (Statiz 로그인 + 크롤링)
- 베이스: `baseball-sim/blend-stats.mjs` (앙상블 로직 참고)
- 베이스: `baseball-sim/predict-snapshot.mjs` (시점 백테스트 패턴)

## 부록 B. 환경 변수 (.env)

```
# DB
DATABASE_URL=postgresql://user:pass@localhost:5432/kbo_predict
REDIS_URL=redis://localhost:6379/0

# Statiz
STATIZ_USER=...
STATIZ_PASS=...

# APIs
WEATHER_API_KEY=...
CLAUDE_API_KEY=...

# ML
MODEL_VERSION=v1.0-xgb+lstm
XGBOOST_ARTIFACT_PATH=backend/app/ml/artifacts/kbo_xgb_v1.pkl
LSTM_ARTIFACT_PATH=backend/app/ml/artifacts/kbo_lstm_v1.pt
```

---

> **문서 작성**: 2026년 5월
> **버전**: v1.0 (데이터 + ML/DL 상세 설계)
> **다음 단계**: A·B 팀원과 피처 리스트 / 함수 시그니처 합의 → 코드 작성 시작
