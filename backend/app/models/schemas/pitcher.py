from typing import Optional

from pydantic import BaseModel


class PitcherGameRecord(BaseModel):
    game_id: int
    innings_pitched: Optional[float] = None
    earned_runs: Optional[int] = None
    strikeouts: Optional[int] = None
    walks: Optional[int] = None
    hits_allowed: Optional[int] = None
    era: Optional[float] = None
    whip: Optional[float] = None

    model_config = {"from_attributes": True}


class PitcherStatsResponse(BaseModel):
    player_id: int
    name: str
    team_name: str
    recent_games: list[PitcherGameRecord]
