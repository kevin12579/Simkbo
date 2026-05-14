from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.utils.logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/predictions/trigger", summary="예측 수동 트리거")
def trigger_predictions(db: Session = Depends(get_db)):
    """스케줄러 오류 시 예측을 수동으로 실행합니다."""
    try:
        from app.services.prediction_service import predict_all_today_games
        results = predict_all_today_games(db)
        return {"status": "ok", "predicted": len(results)}
    except Exception as e:
        logger.error(f"수동 예측 트리거 실패: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/cache/clear", summary="Redis 캐시 초기화")
def clear_cache():
    """예측 캐시를 초기화합니다 (예측 업데이트 후 사용)."""
    from app.db.redis_client import delete_cache_pattern
    delete_cache_pattern("predictions:*")
    delete_cache_pattern("prediction:*")
    return {"status": "ok", "message": "캐시 초기화 완료"}
