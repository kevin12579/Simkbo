"""
단일 경기에 대한 피처 벡터(23개) 생성.

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
from sqlalchemy.orm import Session

from app.models.db.game import Game
from app.models.db.team import Team
from app.models.db.player import Player
from app.models.db.team_snapshot import TeamDailySnapshot
from app.models.db.player_season_stats import PlayerSeasonStats

# 피처 컬럼 순서 (변경 금지 - 모델 아티팩트와 동기화)
# 데이터가 실제로 존재하는 피처만 포함 (23개)
FEATURE_COLUMNS = [
    # 그룹 1: 팀 누적 통계 (team_daily_snapshots)
    "home_season_win_rate", "away_season_win_rate",
    "home_last10_win_rate", "away_last10_win_rate",
    "home_home_win_rate", "away_away_win_rate",
    "home_streak", "away_streak",
    # 그룹 2: 최근 10경기 득실차 (games 테이블)
    "home_run_diff_last10", "away_run_diff_last10",
    # 그룹 3: 불펜 ERA (player_season_stats)
    "home_bullpen_era", "away_bullpen_era",
    # 그룹 4: H2H & 컨텍스트
    "h2h_home_win_rate",
    "rest_diff", "is_weekend", "is_dome",
    # 그룹 5: 차이값 피처
    "last10_wr_diff", "season_wr_diff",
    "bullpen_era_diff", "streak_diff",
    "home_win_rate_diff", "run_diff_diff", "h2h_diff",
]
# 총 23개, 순서 변경 금지


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
        DataFrame shape (1, 23) — FEATURE_COLUMNS 순서
    """
    game = db.query(Game).get(game_id)
    if not game:
        raise ValueError(f"game_id={game_id} 없음")

    cutoff = as_of_date if as_of_date else game.scheduled_at.date() - timedelta(days=1)

    home_snap = _get_team_snapshot(game.home_team_id, cutoff, db)
    away_snap = _get_team_snapshot(game.away_team_id, cutoff, db)

    home_run_diff = _get_run_diff_last10(game.home_team_id, cutoff, db)
    away_run_diff = _get_run_diff_last10(game.away_team_id, cutoff, db)

    home_bullpen_era = _get_bullpen_era(game.home_team_id, None, game.season, db)
    away_bullpen_era = _get_bullpen_era(game.away_team_id, None, game.season, db)

    home_home_wr = _get_home_away_win_rate(game.home_team_id, "home", cutoff, db)
    away_away_wr = _get_home_away_win_rate(game.away_team_id, "away", cutoff, db)

    h2h = _get_h2h_win_rate(game.home_team_id, game.away_team_id, cutoff, db)
    rest_diff = _get_rest_diff(game, cutoff, db)

    is_weekend = 1 if game.scheduled_at.weekday() >= 5 else 0
    # game.home_team.is_dome 를 사용 (stadium 문자열 비교보다 정확)
    home_team = db.query(Team).get(game.home_team_id)
    is_dome = 1 if (home_team and home_team.is_dome) else 0

    home_season_wr = float(home_snap.season_win_rate) if home_snap and home_snap.season_win_rate else 0.5
    away_season_wr = float(away_snap.season_win_rate) if away_snap and away_snap.season_win_rate else 0.5
    home_last10_wr = (home_snap.last10_wins / 10) if home_snap and home_snap.last10_wins is not None else 0.5
    away_last10_wr = (away_snap.last10_wins / 10) if away_snap and away_snap.last10_wins is not None else 0.5

    home_streak_val = 0
    if home_snap:
        home_streak_val = home_snap.streak_count if home_snap.streak_type == "WIN" else -(home_snap.streak_count or 0)
    away_streak_val = 0
    if away_snap:
        away_streak_val = away_snap.streak_count if away_snap.streak_type == "WIN" else -(away_snap.streak_count or 0)

    features = {
        "home_season_win_rate": home_season_wr,
        "away_season_win_rate": away_season_wr,
        "home_last10_win_rate": home_last10_wr,
        "away_last10_win_rate": away_last10_wr,
        "home_home_win_rate": home_home_wr,
        "away_away_win_rate": away_away_wr,
        "home_streak": home_streak_val,
        "away_streak": away_streak_val,
        "home_run_diff_last10": home_run_diff,
        "away_run_diff_last10": away_run_diff,
        "home_bullpen_era": home_bullpen_era,
        "away_bullpen_era": away_bullpen_era,
        "h2h_home_win_rate": h2h,
        "rest_diff": rest_diff,
        "is_weekend": is_weekend,
        "is_dome": is_dome,
        "last10_wr_diff": home_last10_wr - away_last10_wr,
        "season_wr_diff": home_season_wr - away_season_wr,
        "bullpen_era_diff": away_bullpen_era - home_bullpen_era,
        "streak_diff": home_streak_val - away_streak_val,
        "home_win_rate_diff": home_home_wr - away_away_wr,
        "run_diff_diff": home_run_diff - away_run_diff,
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



def _get_run_diff_last10(team_id: int, cutoff: date, db: Session) -> float:
    recent = (
        db.query(Game)
        .filter(
            ((Game.home_team_id == team_id) | (Game.away_team_id == team_id)),
            Game.scheduled_at <= cutoff,
            Game.status == "COMPLETED",
            Game.home_score.isnot(None),
        )
        .order_by(Game.scheduled_at.desc())
        .limit(10)
        .all()
    )
    if not recent:
        return 0.0
    diffs = []
    for g in recent:
        if g.home_team_id == team_id:
            diffs.append(float((g.home_score or 0) - (g.away_score or 0)))
        else:
            diffs.append(float((g.away_score or 0) - (g.home_score or 0)))
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
    wins = sum(1 for g in games if g.home_score is not None and g.home_score > g.away_score)
    return wins / len(games)


def _get_rest_diff(game: Game, cutoff: date, db: Session) -> int:
    def last_game_date(team_id):
        g = (
            db.query(Game)
            .filter(
                ((Game.home_team_id == team_id) | (Game.away_team_id == team_id)),
                Game.id != game.id,
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
        wins = sum(1 for g in games if g.home_score is not None and g.home_score > g.away_score)
    else:
        wins = sum(1 for g in games if g.away_score is not None and g.away_score > g.home_score)
    return wins / len(games)


def _get_bullpen_era(team_id: int, starter_id: Optional[int], season: int, db: Session) -> float:
    pitchers = db.query(Player).filter_by(team_id=team_id, position="PITCHER", is_active=True).all()
    eras = []
    for p in pitchers:
        if p.id == starter_id:
            continue
        stats = db.query(PlayerSeasonStats).filter_by(player_id=p.id, season=season).first()
        if stats and stats.era and float(stats.era) < 10.0:
            eras.append(float(stats.era))
    return sum(eras) / len(eras) if eras else 4.50
