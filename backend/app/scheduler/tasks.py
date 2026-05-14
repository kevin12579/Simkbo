from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.database import SessionLocal
from app.utils.logger import logger

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def morning_task():
    """매일 06:00 — 전날 경기 결과 + 팀 순위 수집"""
    logger.info("[스케줄러] 오전 수집 태스크 시작")
    db = SessionLocal()
    try:
        # AI 파트 pipeline 완성 후 활성화
        # from app.crawler.pipeline import run_morning_pipeline
        # run_morning_pipeline(db)
        logger.info("[스케줄러] 오전 수집 완료 (pipeline 미연동)")
    except Exception as e:
        logger.error(f"[스케줄러] 오전 수집 실패: {e}")
    finally:
        db.close()


def evening_task():
    """매일 18:00 — 선발 투수 + 날씨 수집"""
    logger.info("[스케줄러] 오후 수집 태스크 시작")
    db = SessionLocal()
    try:
        from app.crawler.pipeline import run_evening_pipeline
        run_evening_pipeline(db)
        logger.info("[스케줄러] 오후 수집 완료")
    except Exception as e:
        logger.error(f"[스케줄러] 오후 수집 실패: {e}")
    finally:
        db.close()


def prediction_task():
    """매일 19:30 — ML 추론 + Claude AI 근거 생성"""
    logger.info("[스케줄러] 예측 태스크 시작")
    db = SessionLocal()
    try:
        from app.services.prediction_service import predict_all_today_games
        results = predict_all_today_games(db)
        # 예측 완료 후 캐시 무효화
        from app.db.redis_client import delete_cache_pattern
        delete_cache_pattern("predictions:*")
        delete_cache_pattern("prediction:*")
        logger.info(f"[스케줄러] 예측 완료: {len(results)}경기")
    except Exception as e:
        logger.error(f"[스케줄러] 예측 실패: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(morning_task, CronTrigger(hour=6, minute=0), max_instances=1, id="morning")
    scheduler.add_job(evening_task, CronTrigger(hour=18, minute=0), max_instances=1, id="evening")
    scheduler.add_job(prediction_task, CronTrigger(hour=19, minute=30), max_instances=1, id="prediction")
    scheduler.start()
    logger.info("APScheduler 시작 — 매일 06:00 / 18:00 / 19:30 자동 실행")


def stop_scheduler():
    scheduler.shutdown()
