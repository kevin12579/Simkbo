from sqlalchemy import Column, Integer, Numeric, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class GamePrediction(Base):
    __tablename__ = "game_predictions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    home_starter_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    away_starter_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    home_win_prob = Column(Numeric(5, 4))
    away_win_prob = Column(Numeric(5, 4))
    confidence_level = Column(String(10))   # "HIGH" | "MEDIUM" | "LOW"
    xgboost_home_prob = Column(Numeric(5, 4))
    lstm_home_prob = Column(Numeric(5, 4))
    model_version = Column(String(50))
    features_used = Column(Integer)
    prediction_reason = Column(String(2000))  # Claude API 생성 근거
    is_final = Column(Boolean, default=False)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="predictions")
    home_starter = relationship("Player", foreign_keys=[home_starter_id])
    away_starter = relationship("Player", foreign_keys=[away_starter_id])
