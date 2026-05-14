from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(SmallInteger, nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score = Column(SmallInteger)
    away_score = Column(SmallInteger)
    # "SCHEDULED" | "IN_PROGRESS" | "COMPLETED" | "POSTPONED" | "CANCELLED"
    status = Column(String(20), default="SCHEDULED", nullable=False, index=True)
    stadium = Column(String(100))

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    predictions = relationship("GamePrediction", back_populates="game")
    pitcher_game_stats = relationship("PitcherGameStats", back_populates="game")
    team_game_stats = relationship("TeamGameStats", back_populates="game")
