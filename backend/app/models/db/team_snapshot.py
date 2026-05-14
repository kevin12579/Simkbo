from sqlalchemy import Column, Integer, SmallInteger, Date, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TeamDailySnapshot(Base):
    __tablename__ = "team_daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    rank = Column(SmallInteger)
    games_played = Column(SmallInteger)
    wins = Column(SmallInteger)
    losses = Column(SmallInteger)
    draws = Column(SmallInteger)
    season_win_rate = Column(Numeric(4, 3))
    last10_wins = Column(SmallInteger)
    last10_losses = Column(SmallInteger)
    streak_type = Column(String(10))   # "WIN" | "LOSS" | "DRAW"
    streak_count = Column(SmallInteger)
    created_at = Column(DateTime, server_default=func.now())

    team = relationship("Team", back_populates="snapshots")

    __table_args__ = (UniqueConstraint("team_id", "snapshot_date"),)
