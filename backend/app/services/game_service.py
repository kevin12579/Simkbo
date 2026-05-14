from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from app.db.redis_client import get_cache, set_cache
from app.models.db.game import Game
from app.models.db.prediction import GamePrediction

CACHE_TTL = 1800  # 30분


def get_today_games(db: Session, target_date: date = None) -> dict:
    if target_date is None:
        target_date = date.today()

    cache_key = f"predictions:today:{target_date.isoformat()}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    games = (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .filter(
            Game.scheduled_at >= target_date,
            Game.scheduled_at < target_date + timedelta(days=1),
        )
        .order_by(Game.scheduled_at)
        .all()
    )

    result_games = [_format_game_card(g, _get_latest_final_prediction(g.id, db), db) for g in games]

    response = {
        "date": target_date.isoformat(),
        "games": result_games,
        "total": len(result_games),
    }
    set_cache(cache_key, response, CACHE_TTL)
    return response


def get_game_prediction_detail(game_id: int, db: Session) -> dict | None:
    cache_key = f"prediction:detail:{game_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    game = (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .filter(Game.id == game_id)
        .first()
    )
    if not game:
        return None

    prediction = _get_latest_final_prediction(game_id, db)
    result = _format_game_card(game, prediction, db)

    # 상세 페이지는 ai_reasoning 포함이므로 별도 캐시
    set_cache(cache_key, result, CACHE_TTL)
    return result


def _get_latest_final_prediction(game_id: int, db: Session):
    return (
        db.query(GamePrediction)
        .filter(GamePrediction.game_id == game_id, GamePrediction.is_final == True)
        .order_by(GamePrediction.predicted_at.desc())
        .first()
    )


def _format_game_card(game: Game, prediction: GamePrediction, db: Session) -> dict:
    from app.models.db.player import Player

    data = {
        "game_id": game.id,
        "scheduled_at": game.scheduled_at.isoformat(),
        "stadium": game.stadium,
        "status": game.status,
        "home_team": {
            "id": game.home_team.id,
            "name": game.home_team.full_name,
            "short_name": game.home_team.short_name,
            "logo_url": None,
        },
        "away_team": {
            "id": game.away_team.id,
            "name": game.away_team.full_name,
            "short_name": game.away_team.short_name,
            "logo_url": None,
        },
        "prediction": None,
    }

    if prediction:
        home_starter = None
        away_starter = None

        if prediction.home_starter_id:
            p = db.query(Player).get(prediction.home_starter_id)
            if p:
                home_starter = {"player_id": p.id, "name": p.name, "recent_era": None}

        if prediction.away_starter_id:
            p = db.query(Player).get(prediction.away_starter_id)
            if p:
                away_starter = {"player_id": p.id, "name": p.name, "recent_era": None}

        data["prediction"] = {
            "home_win_prob": float(prediction.home_win_prob) if prediction.home_win_prob else None,
            "away_win_prob": float(prediction.away_win_prob) if prediction.away_win_prob else None,
            "confidence_level": prediction.confidence_level,
            "xgboost_home_prob": float(prediction.xgboost_home_prob) if prediction.xgboost_home_prob else None,
            "lstm_home_prob": float(prediction.lstm_home_prob) if prediction.lstm_home_prob else None,
            "ai_reasoning": prediction.prediction_reason,
            "home_starter": home_starter,
            "away_starter": away_starter,
            "updated_at": prediction.predicted_at.isoformat(),
        }

    return data
