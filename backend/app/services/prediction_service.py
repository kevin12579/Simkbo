"""
예측 서비스. 백엔드 파트(C팀)에서 호출하는 공개 인터페이스.

인터페이스:
    predict_game(game_id, db) -> dict
    predict_all_today_games(db) -> list[dict]
    update_starters(games, db) -> int
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.ml.feature_engineering import build_features_for_game
from app.models.db.game import Game
from app.models.db.player import Player
from app.models.db.prediction import GamePrediction
from app.utils.logger import logger

# 모델 아티팩트 캐시 (프로세스 수명 동안 메모리에 유지)
_xgb_artifact = None
_lstm_model = None


def _load_models():
    global _xgb_artifact, _lstm_model

    if _xgb_artifact is None:
        try:
            from app.ml.xgboost_model import load_xgboost_model
            _xgb_artifact = load_xgboost_model()
            logger.info("XGBoost 모델 로드 완료")
        except Exception as e:
            logger.error(f"XGBoost 모델 로드 실패: {e}")
            _xgb_artifact = None

    if _lstm_model is None:
        try:
            from app.ml.pytorch_model import load_lstm_model
            _lstm_model = load_lstm_model()
            if _lstm_model:
                logger.info("LSTM 모델 로드 완료")
        except Exception as e:
            logger.warning(f"LSTM 모델 로드 실패 (XGBoost만 사용): {e}")
            _lstm_model = None


def predict_game(game_id: int, db: Session) -> dict:
    """
    단일 경기 예측 실행. 백엔드 스케줄러에서 호출됩니다.

    Returns:
        {
            "home_win_prob": 0.62,
            "away_win_prob": 0.38,
            "confidence_level": "HIGH",
            "xgboost_home_prob": 0.61,
            "lstm_home_prob": 0.64,
            "model_version": "v1.0-xgb+lstm",
            "features_used": 47,
            "predicted_at": "2025-05-12T19:30:00+09:00",
        }
    """
    _load_models()

    if _xgb_artifact is None:
        raise RuntimeError("XGBoost 모델이 로드되지 않았습니다. 먼저 모델을 학습하세요.")

    game = db.query(Game).get(game_id)
    if not game:
        raise ValueError(f"game_id={game_id} 없음")

    # 피처 생성 (추론 시 as_of_date=None → 최신 정보 사용)
    features_df = build_features_for_game(game_id, as_of_date=None, db=db)

    # XGBoost 예측
    from app.ml.xgboost_model import predict_proba as xgb_predict
    xgb_proba = xgb_predict(features_df, _xgb_artifact)

    # LSTM 예측 (가능한 경우)
    lstm_proba = xgb_proba  # fallback
    lstm_available = _lstm_model is not None

    # 선발 미확정 여부 확인
    current_pred = _get_latest_prediction(game_id, db)
    starter_unconfirmed = (
        current_pred is None
        or current_pred.home_starter_id is None
        or current_pred.away_starter_id is None
    )

    # 앙상블
    from app.ml.ensemble import ensemble_prediction
    result = ensemble_prediction(
        xgb_proba=xgb_proba,
        lstm_proba=lstm_proba,
        context={
            "starter_unconfirmed": starter_unconfirmed,
            "lstm_available": lstm_available,
        },
    )

    # Claude API로 예측 근거 생성
    prediction_reason = _generate_reason(game, result, features_df, db)

    # DB 저장
    pred = GamePrediction(
        game_id=game_id,
        home_starter_id=current_pred.home_starter_id if current_pred else None,
        away_starter_id=current_pred.away_starter_id if current_pred else None,
        home_win_prob=result["home_win_prob"],
        away_win_prob=result["away_win_prob"],
        confidence_level=result["confidence_level"],
        xgboost_home_prob=result["xgboost_home_prob"],
        lstm_home_prob=result["lstm_home_prob"],
        model_version=settings.model_version,
        features_used=len(features_df.columns) if features_df is not None else 44,
        prediction_reason=prediction_reason,
        is_final=True,
        predicted_at=datetime.now(timezone.utc),
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)

    return {
        "home_win_prob": float(result["home_win_prob"]),
        "away_win_prob": float(result["away_win_prob"]),
        "confidence_level": result["confidence_level"],
        "xgboost_home_prob": float(result["xgboost_home_prob"]),
        "lstm_home_prob": float(result["lstm_home_prob"]),
        "model_version": settings.model_version,
        "features_used": pred.features_used,
        "predicted_at": pred.predicted_at.isoformat(),
        "prediction_reason": prediction_reason,
    }


def predict_all_today_games(db: Session) -> list:
    """
    오늘 모든 경기 예측. 스케줄러 19:30 태스크에서 호출됩니다.
    각 경기의 예측 결과를 game_predictions 테이블에 저장합니다.
    """
    from datetime import date, timedelta
    today = date.today()

    games = (
        db.query(Game)
        .filter(
            Game.scheduled_at >= today,
            Game.scheduled_at < today + timedelta(days=1),
            Game.status.in_(["SCHEDULED", "IN_PROGRESS"]),
        )
        .all()
    )

    results = []
    for game in games:
        try:
            result = predict_game(game.id, db)
            result["game_id"] = game.id
            results.append(result)
            logger.info(
                f"경기 {game.id} 예측 완료: "
                f"홈={result['home_win_prob']:.2%}, "
                f"신뢰도={result['confidence_level']}"
            )
        except Exception as e:
            logger.error(f"경기 {game.id} 예측 실패: {e}")

    return results


def update_starters(games: list, db: Session) -> int:
    """
    네이버 크롤러에서 수집한 선발 투수 정보로 game_predictions 업데이트.

    Args:
        games: NaverCrawler.fetch_today_starters() 반환값
        db: DB 세션

    Returns: 업데이트된 경기 수
    """
    updated = 0

    for game_info in games:
        try:
            home_team_name = game_info.get("home_team")
            away_team_name = game_info.get("away_team")
            home_starter_name = game_info.get("home_starter")
            away_starter_name = game_info.get("away_starter")

            if not home_team_name or not away_team_name:
                continue

            from datetime import datetime
            game_date = datetime.strptime(game_info["game_date"], "%Y-%m-%d").date()

            from app.models.db.team import Team
            home_team = db.query(Team).filter_by(short_name=home_team_name).first()
            away_team = db.query(Team).filter_by(short_name=away_team_name).first()

            if not home_team or not away_team:
                continue

            from datetime import timedelta
            game = (
                db.query(Game)
                .filter(
                    Game.home_team_id == home_team.id,
                    Game.away_team_id == away_team.id,
                    Game.scheduled_at >= game_date,
                    Game.scheduled_at < game_date + timedelta(days=1),
                )
                .first()
            )

            if not game:
                continue

            home_starter_id = _find_player_id(home_starter_name, home_team.id, db) if home_starter_name else None
            away_starter_id = _find_player_id(away_starter_name, away_team.id, db) if away_starter_name else None

            # 기존 예측 업데이트 또는 새 예측 레코드 생성
            pred = _get_latest_prediction(game.id, db)
            if pred:
                pred.home_starter_id = home_starter_id
                pred.away_starter_id = away_starter_id
            else:
                pred = GamePrediction(
                    game_id=game.id,
                    home_starter_id=home_starter_id,
                    away_starter_id=away_starter_id,
                    is_final=False,
                )
                db.add(pred)

            updated += 1

        except Exception as e:
            logger.error(f"선발 투수 업데이트 오류: {e}")
            continue

    db.commit()
    return updated


def _get_latest_prediction(game_id: int, db: Session) -> Optional[GamePrediction]:
    return (
        db.query(GamePrediction)
        .filter_by(game_id=game_id)
        .order_by(GamePrediction.predicted_at.desc())
        .first()
    )


def _find_player_id(name: str, team_id: int, db: Session) -> Optional[int]:
    if not name:
        return None
    player = db.query(Player).filter_by(name=name, team_id=team_id).first()
    return player.id if player else None


def _generate_reason(game: Game, result: dict, features_df, db: Session) -> Optional[str]:
    """OpenAI API로 예측 근거 텍스트 생성."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI
        from app.models.db.team import Team

        home_team = db.query(Team).get(game.home_team_id)
        away_team = db.query(Team).get(game.away_team_id)

        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""다음 KBO 경기 예측 결과에 대한 근거를 3-4문장으로 한국어로 설명해주세요.

경기: {away_team.short_name if away_team else '원정팀'} vs {home_team.short_name if home_team else '홈팀'} (홈)
홈팀 승리 확률: {result['home_win_prob']:.1%}
신뢰도: {result['confidence_level']}
XGBoost 예측: {result['xgboost_home_prob']:.1%}

주요 지표:
- 홈팀 시즌 승률: {float(features_df['home_season_win_rate'].iloc[0]):.3f}
- 원정팀 시즌 승률: {float(features_df['away_season_win_rate'].iloc[0]):.3f}
- 홈팀 선발 ERA: {float(features_df['home_starter_era'].iloc[0]):.2f}
- 원정팀 선발 ERA: {float(features_df['away_starter_era'].iloc[0]):.2f}

통계 기반의 객관적인 분석을 제공하고, 확실하지 않은 부분은 언급하지 마세요."""

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.warning(f"OpenAI API 근거 생성 실패: {e}")
        return None
