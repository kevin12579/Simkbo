from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.game_service import get_game_prediction_detail, get_today_games
from app.utils.exceptions import GameNotFoundException

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/today", summary="오늘의 경기 예측 목록")
def today_games(
    target_date: date = Query(default=None, description="조회 날짜 (YYYY-MM-DD). 기본값: 오늘"),
    db: Session = Depends(get_db),
):
    return get_today_games(db, target_date)


@router.get("/{game_id}/prediction", summary="경기 상세 예측")
def game_prediction(game_id: int, db: Session = Depends(get_db)):
    result = get_game_prediction_detail(game_id, db)
    if not result:
        raise GameNotFoundException(game_id)
    return result
