from sqlalchemy import Column, Integer, SmallInteger, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class PlayerSeasonStats(Base):
    __tablename__ = "player_season_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    season = Column(SmallInteger, nullable=False)
    # 타자 스탯
    avg = Column(Numeric(4, 3))
    obp = Column(Numeric(4, 3))
    slg = Column(Numeric(4, 3))
    ops = Column(Numeric(5, 3))
    hr = Column(SmallInteger)
    rbi = Column(SmallInteger)
    sb = Column(SmallInteger)
    war_batter = Column(Numeric(4, 2))
    # 투수 스탯
    era = Column(Numeric(5, 2))
    whip = Column(Numeric(5, 2))
    fip = Column(Numeric(5, 2))
    innings_pitched = Column(Numeric(5, 1))
    strikeouts = Column(SmallInteger)
    walks = Column(SmallInteger)
    war_pitcher = Column(Numeric(4, 2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    player = relationship("Player", back_populates="season_stats")

    __table_args__ = (UniqueConstraint("player_id", "season"),)
