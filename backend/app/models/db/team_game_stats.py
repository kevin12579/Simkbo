from sqlalchemy import Column, Integer, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class TeamGameStats(Base):
    __tablename__ = "team_game_stats"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    runs_scored = Column(SmallInteger)
    runs_allowed = Column(SmallInteger)
    hits = Column(SmallInteger)
    errors = Column(SmallInteger)

    team = relationship("Team")
    game = relationship("Game", back_populates="team_game_stats")
