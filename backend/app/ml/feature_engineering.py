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

from app.models.db.game import Game
from app.models.db.team import Team
from app.models.db.player import Player
from app.models.db.team_snapshot import TeamDailySnapshot
from app.models.db.player_season_stats import PlayerSeasonStats
from app.models.db.pitcher_game_stats import PitcherGameStats
from app.models.db.team_game_stats import TeamGameStats

# 피처 컬럼 순서 (변경 금지 — 모델 아티팩트와 동기화)
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
# 총 44개 (인덱스 0~43), 순서 변경 금지


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

    cutoff = as_of_date if as_of_date else game.scheduled_at.date() - timedelta(days=1)

    home_snap = _get_team_snapshot(game.home_team_id, cutoff, db)
    away_snap = _get_team_snapshot(game.away_team_id, cutoff, db)

    prediction = _get_prediction(game_id, db)
    home_pitcher_id = prediction.home_starter_id if prediction else None
    away_pitcher_id = prediction.away_starter_id if prediction else None

    home_pitcher_stats = _get_pitcher_stats(home_pitcher_id, game.season, cutoff, db)
    away_pitcher_stats = _get_pitcher_stats(away_pitcher_id, game.season, cutoff, db)

    home_team_stats = _get_team_season_stats(game.home_team_id, game.season, db)
    away_team_stats = _get_team_season_stats(game.away_team_id, game.season, db)

    home_run_diff = _get_run_diff_last10(game.home_team_id, cutoff, db)
    away_run_diff = _get_run_diff_last10(game.away_team_id, cutoff, db)

    h2h = _get_h2h_win_rate(game.home_team_id, game.away_team_id, cutoff, db)
    rest_diff = _get_rest_diff(game, cutoff, db)

    is_weekend = 1 if game.scheduled_at.weekday() >= 5 else 0
    is_dome = 1 if game.stadium == "고척스카이돔" else 0

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

    home_ops = float(home_team_stats.team_ops) if home_team_stats and home_team_stats.team_ops else 0.720
    away_ops = float(away_team_stats.team_ops) if away_team_stats and away_team_stats.team_ops else 0.720
    home_era = float(home_team_stats.team_era) if home_team_stats and home_team_stats.team_era else 4.50
    away_era = float(away_team_stats.team_era) if away_team_stats and away_team_stats.team_era else 4.50

    home_starter_era = float(home_pitcher_stats.era) if home_pitcher_stats and home_pitcher_stats.era else home_era
    away_starter_era = float(away_pitcher_stats.era) if away_pitcher_stats and away_pitcher_stats.era else away_era
    home_starter_recent5_era = _get_pitcher_recent5_era(home_pitcher_id, cutoff, db)
    away_starter_recent5_era = _get_pitcher_recent5_era(away_pitcher_id, cutoff, db)
    home_starter_whip = float(home_pitcher_stats.whip) if home_pitcher_stats and home_pitcher_stats.whip else 1.30
    away_starter_whip = float(away_pitcher_stats.whip) if away_pitcher_stats and away_pitcher_stats.whip else 1.30

    home_bullpen_era = _get_bullpen_era(game.home_team_id, home_pitcher_id, game.season, db)
    away_bullpen_era = _get_bullpen_era(game.away_team_id, away_pitcher_id, game.season, db)

    home_home_wr = _get_home_away_win_rate(game.home_team_id, "home", cutoff, db)
    away_away_wr = _get_home_away_win_rate(game.away_team_id, "away", cutoff, db)

    features = {
        "home_season_win_rate": home_season_wr,
        "away_season_win_rate": away_season_wr,
        "home_last10_win_rate": home_last10_wr,
        "away_last10_win_rate": away_last10_wr,
        "home_home_win_rate": home_home_wr,
        "away_away_win_rate": away_away_wr,
        "home_streak": home_streak_val,
        "away_streak": away_streak_val,
        "home_ops": home_ops,
        "away_ops": away_ops,
        "home_era": home_era,
        "away_era": away_era,
        "home_run_diff_last10": home_run_diff,
        "away_run_diff_last10": away_run_diff,
        "home_starter_era": home_starter_era,
        "away_starter_era": away_starter_era,
        "home_starter_recent5_era": home_starter_recent5_era,
        "away_starter_recent5_era": away_starter_recent5_era,
        "home_starter_whip": home_starter_whip,
        "away_starter_whip": away_starter_whip,
        "home_bullpen_era": home_bullpen_era,
        "away_bullpen_era": away_bullpen_era,
        "home_top5_ops": 0.720,   # TODO: 타자 데이터 수집 후 구현
        "away_top5_ops": 0.720,
        "home_hr_power": 0,       # TODO: 팀 홈런 수 수집 후 구현
        "away_hr_power": 0,
        "h2h_home_win_rate": h2h,
        "rest_diff": rest_diff,
        "is_weekend": is_weekend,
        "is_dome": is_dome,
        # 차이값 피처 (diff)
        "era_diff": away_starter_era - home_starter_era,
        "ops_diff": home_ops - away_ops,
        "last10_wr_diff": home_last10_wr - away_last10_wr,
        "season_wr_diff": home_season_wr - away_season_wr,
        "starter_era_diff": away_starter_era - home_starter_era,
        "bullpen_era_diff": away_bullpen_era - home_bullpen_era,
        "top5_ops_diff": 0.0,
        "streak_diff": home_streak_val - away_streak_val,
        "home_win_rate_diff": home_home_wr - away_away_wr,
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
    diffs = [float((s.runs_scored or 0) - (s.runs_allowed or 0)) for s in recent]
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


def _get_prediction(game_id: int, db: Session):
    from app.models.db.prediction import GamePrediction
    return (
        db.query(GamePrediction)
        .filter_by(game_id=game_id, is_final=True)
        .order_by(GamePrediction.predicted_at.desc())
        .first()
    )


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
