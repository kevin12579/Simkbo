from sqlalchemy import Column, Integer, SmallInteger, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class PitcherGameStats(Base):
    __tablename__ = "pitcher_game_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    is_starter = Column(Boolean, default=False)
    innings_pitched = Column(Numeric(5, 1))
    earned_runs = Column(SmallInteger)
    strikeouts = Column(SmallInteger)
    walks = Column(SmallInteger)
    hits_allowed = Column(SmallInteger)
    era = Column(Numeric(5, 2))    # 해당 경기 기준 시즌 ERA
    whip = Column(Numeric(5, 2))   # 해당 경기 기준 시즌 WHIP

    player = relationship("Player", back_populates="pitcher_game_stats")
    game = relationship("Game", back_populates="pitcher_game_stats")
