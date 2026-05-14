from typing import Optional

from pydantic import BaseModel


class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: str
    stadium: Optional[str] = None
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RecentRecord(BaseModel):
    last_n_games: int
    wins: int
    losses: int
    win_rate: float
    avg_runs_scored: float
    home_record: dict
    away_record: dict
    streak: str


class TeamStatsResponse(BaseModel):
    team: TeamResponse
    recent_stats: RecentRecord
    updated_at: str
