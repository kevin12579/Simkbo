from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.team_service import get_all_teams, get_team_stats
from app.utils.exceptions import TeamNotFoundException

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", summary="KBO 10개 구단 목록")
def list_teams(db: Session = Depends(get_db)):
    return get_all_teams(db)


@router.get("/{team_id}/stats", summary="팀 최근 통계")
def team_stats(team_id: int, db: Session = Depends(get_db)):
    result = get_team_stats(team_id, db)
    if not result:
        raise TeamNotFoundException(team_id)
    return result
