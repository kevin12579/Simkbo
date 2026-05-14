"""
크롤링 통합 실행기. APScheduler에서 이 함수들을 호출합니다.

수동 실행 예시:
    python -c "
    from app.db.database import SessionLocal
    from app.crawler.pipeline import run_morning_pipeline
    db = SessionLocal()
    run_morning_pipeline(db)
    db.close()
    "
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.crawler.kbo_official_crawler import KBOOfficialCrawler
from app.crawler.statiz_crawler import StatizCrawler
from app.crawler.naver_crawler import NaverCrawler
from app.utils.logger import logger


def run_morning_pipeline(db: Session) -> dict:
    """
    매일 06:00 실행.
    - 전날 팀 순위 스냅샷 수집 (KBO 공식)
    - 선수 시즌 통계 갱신 (Statiz)
    """
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    season = date.today().year
    results = {}

    # 1. 팀 순위 스냅샷 저장
    logger.info("팀 순위 수집 시작...")
    kbo_crawler = KBOOfficialCrawler()
    try:
        count = kbo_crawler.save_team_snapshots(yesterday, db)
        results["team_snapshots"] = count
        kbo_crawler.log_crawl_result(db, "kbo_official", "team_rank", "SUCCESS", count)
        logger.info(f"팀 순위 {count}개 저장")
    except Exception as e:
        logger.error(f"팀 순위 수집 실패: {e}")
        kbo_crawler.log_crawl_result(db, "kbo_official", "team_rank", "FAILED", 0, str(e))
        results["team_snapshots"] = 0

    # 2. Statiz 투수 통계 갱신
    logger.info("Statiz 투수 통계 수집 시작...")
    statiz = StatizCrawler()
    try:
        count = statiz.sync_all_pitchers(db, season)
        results["pitcher_stats"] = count
        statiz.log_crawl_result(db, "statiz", "pitcher_season_stats", "SUCCESS", count)
        logger.info(f"투수 통계 {count}명 저장")
    except Exception as e:
        logger.error(f"Statiz 수집 실패: {e}")
        statiz.log_crawl_result(db, "statiz", "pitcher_season_stats", "FAILED", 0, str(e))
        results["pitcher_stats"] = 0

    return results


def run_evening_pipeline(db: Session) -> dict:
    """
    매일 18:00 실행.
    - 당일 선발 투수 확정 정보 수집 (네이버)
    - 선발 미확정 경기는 confidence_level='LOW' 로 1차 예측 저장
    """
    logger.info("오후 파이프라인 시작...")
    naver = NaverCrawler()

    try:
        games = naver.fetch_today_starters()

        from app.services.prediction_service import update_starters
        count = update_starters(games, db)

        logger.info(f"선발 투수 {count}경기 업데이트")
        return {"updated_games": count}

    except Exception as e:
        logger.error(f"오후 파이프라인 실패: {e}")
        return {"error": str(e)}


def run_ml_pipeline(db: Session) -> dict:
    """
    매일 19:30 실행.
    - XGBoost + LSTM 앙상블 예측
    - Claude API 근거 생성
    - DB 저장
    """
    logger.info("ML 추론 파이프라인 시작...")
    try:
        from app.services.prediction_service import predict_all_today_games
        results = predict_all_today_games(db)
        logger.info(f"ML 예측 완료: {len(results)}경기")
        return {"predicted_games": len(results)}
    except Exception as e:
        logger.error(f"ML 파이프라인 실패: {e}")
        return {"error": str(e)}


def run_bulk_historical_collection(
    start_date: str,
    end_date: str,
    db: Session,
) -> dict:
    """
    학습 데이터 구축을 위한 과거 데이터 일괄 수집 (최초 1회 실행).
    start_date, end_date: 'YYYYMMDD' 형식

    주의: 수천 번의 요청이 발생하므로 수 시간이 소요됩니다.
    """
    logger.info(f"과거 데이터 수집 시작: {start_date} ~ {end_date}")
    kbo = KBOOfficialCrawler()
    result = kbo.bulk_collect_snapshots(start_date, end_date, db)
    logger.info(f"수집 완료: {result}")
    return result
