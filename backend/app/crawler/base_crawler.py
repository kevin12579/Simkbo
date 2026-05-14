import time
import random
import logging
from typing import Optional

import requests
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class BaseCrawler:

    def __init__(self, delay: float = 2.0, max_retries: int = 3, retry_wait: int = 30):
        self.delay = delay
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self.session = requests.Session()
        self._rotate_ua()

    def _rotate_ua(self):
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def safe_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """안전한 HTTP GET 요청 (재시도 및 지수 백오프 포함)"""
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=15, **kwargs)
                resp.encoding = "utf-8"

                if resp.status_code == 200:
                    time.sleep(self.delay + random.uniform(0, 0.5))
                    return resp

                if resp.status_code in (403, 429):
                    wait_time = self.retry_wait * (attempt + 1)
                    logger.warning(
                        f"[{resp.status_code}] {url} — {wait_time}초 대기 후 재시도 "
                        f"({attempt + 1}/{self.max_retries})"
                    )
                    self._rotate_ua()
                    time.sleep(wait_time)
                    continue

                resp.raise_for_status()

            except requests.RequestException as e:
                logger.error(f"요청 실패: {url} — {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_wait)
                    continue

        logger.error(f"최대 재시도 초과: {url}")
        return None

    def log_crawl_result(
        self,
        db: Session,
        source: str,
        task_type: str,
        status: str,
        records: int = 0,
        error: str = None,
    ):
        """크롤링 결과를 crawl_logs 테이블에 기록합니다."""
        try:
            from app.models.db.crawl_log import CrawlLog
            log = CrawlLog(
                source=source,
                task_type=task_type,
                status=status,
                records_collected=records,
                error_message=error,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"크롤 로그 저장 실패: {e}")
