from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    short_name = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    stadium = Column(String(100))
    is_dome = Column(Boolean, default=False)

    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    snapshots = relationship("TeamDailySnapshot", back_populates="team")
    season_stats = relationship("TeamSeasonStats", back_populates="team")
