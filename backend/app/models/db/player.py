from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    position = Column(String(20))   # "PITCHER" | "BATTER"
    throw_hand = Column(String(10)) # "LEFT" | "RIGHT"
    is_foreign = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    team = relationship("Team", back_populates="players")
    season_stats = relationship("PlayerSeasonStats", back_populates="player")
    pitcher_game_stats = relationship("PitcherGameStats", back_populates="player")
