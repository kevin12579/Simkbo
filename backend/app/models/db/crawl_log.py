from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.db.database import Base


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)       # "kbo_official" | "statiz" | "naver" | "weather"
    task_type = Column(String(50), nullable=False)    # "team_rank" | "pitcher_season_stats" | ...
    status = Column(String(20), nullable=False)       # "SUCCESS" | "FAILED"
    records_collected = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
