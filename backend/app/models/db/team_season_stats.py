from sqlalchemy import Column, Integer, SmallInteger, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TeamSeasonStats(Base):
    __tablename__ = "team_season_stats"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    season = Column(SmallInteger, nullable=False)
    team_ops = Column(Numeric(5, 3))
    team_era = Column(Numeric(5, 2))
    runs_scored = Column(Integer)
    runs_allowed = Column(Integer)
    win_rate = Column(Numeric(4, 3))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    team = relationship("Team", back_populates="season_stats")

    __table_args__ = (UniqueConstraint("team_id", "season"),)
