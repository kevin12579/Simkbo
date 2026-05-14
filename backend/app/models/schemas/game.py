from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamBasic(BaseModel):
    id: int
    name: str
    short_name: str
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class StarterBasic(BaseModel):
    player_id: int
    name: str
    recent_era: Optional[float] = None

    model_config = {"from_attributes": True}


class PredictionCard(BaseModel):
    home_win_prob: float
    away_win_prob: float
    confidence_level: str
    xgboost_home_prob: Optional[float] = None
    lstm_home_prob: Optional[float] = None
    ai_reasoning: Optional[str] = None
    home_starter: Optional[StarterBasic] = None
    away_starter: Optional[StarterBasic] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameCardResponse(BaseModel):
    game_id: int
    scheduled_at: datetime
    stadium: Optional[str] = None
    status: str
    home_team: TeamBasic
    away_team: TeamBasic
    prediction: Optional[PredictionCard] = None

    model_config = {"from_attributes": True}


class TodayGamesResponse(BaseModel):
    date: str
    games: list[GameCardResponse]
    total: int
