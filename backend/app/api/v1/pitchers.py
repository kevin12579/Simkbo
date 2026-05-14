from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.pitcher_service import get_pitcher_stats
from app.utils.exceptions import PlayerNotFoundException

router = APIRouter(prefix="/pitchers", tags=["pitchers"])


@router.get("/{player_id}/stats", summary="투수 최근 5경기 기록")
def pitcher_stats(player_id: int, db: Session = Depends(get_db)):
    result = get_pitcher_stats(player_id, db)
    if not result:
        raise PlayerNotFoundException(player_id)
    return result
