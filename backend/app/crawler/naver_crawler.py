"""
네이버 스포츠에서 당일 선발 투수 및 경기 결과 수집.

선발 투수 확정 시간: 보통 경기 전날 저녁 ~ 당일 오전
확정 전: home_starter_id=NULL, confidence_level='LOW' 로 1차 예측 게시
확정 후: 18:00 크롤링에서 선발 투수 업데이트 + 예측 재실행

주의: 네이버 스포츠는 SPA(React 기반)이므로 Playwright 사용.
"""
import re
from datetime import date
from typing import Optional

from app.crawler.base_crawler import BaseCrawler
from app.utils.logger import logger

NAVER_SPORTS_BASE = "https://sports.naver.com"


class NaverCrawler(BaseCrawler):

    def fetch_today_starters(self, target_date: date = None) -> list[dict]:
        """
        당일 선발 투수 정보 반환.

        Returns:
            [
                {
                    "game_date": "2025-05-12",
                    "home_team": "두산",
                    "away_team": "LG",
                    "home_starter": "곽빈",     # None이면 미확정
                    "away_starter": "임찬규",
                    "game_time": "18:30",
                    "venue": "잠실야구장",
                },
                ...
            ]
        """
        if target_date is None:
            target_date = date.today()

        return self.fetch_with_playwright(target_date)

    def fetch_with_playwright(self, target_date: date = None) -> list[dict]:
        """Playwright를 사용한 SPA 크롤링."""
        from playwright.sync_api import sync_playwright

        if target_date is None:
            target_date = date.today()

        date_str = target_date.strftime("%Y-%m-%d")
        date_param = target_date.strftime("%Y%m%d")
        url = f"{NAVER_SPORTS_BASE}/kbaseball/schedule/index.nhn?date={date_param}"

        games = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)

                game_items = page.query_selector_all(".ScheduleLeagueType_item__McDoB, [class*='ScheduleLeague'] [class*='item']")

                if not game_items:
                    # 대안 셀렉터 시도
                    game_items = page.query_selector_all("li[class*='ScheduleGame'], div[class*='game_item']")

                for item in game_items:
                    try:
                        home_team_el = item.query_selector("[class*='home'] [class*='team_name'], [class*='TeamHome'] [class*='name']")
                        away_team_el = item.query_selector("[class*='away'] [class*='team_name'], [class*='TeamAway'] [class*='name']")
                        home_pitcher_el = item.query_selector("[class*='home'] [class*='pitcher'], [class*='TeamHome'] [class*='pitcher']")
                        away_pitcher_el = item.query_selector("[class*='away'] [class*='pitcher'], [class*='TeamAway'] [class*='pitcher']")
                        time_el = item.query_selector("[class*='time'], [class*='game_time']")
                        venue_el = item.query_selector("[class*='venue'], [class*='stadium']")

                        home_team = home_team_el.inner_text().strip() if home_team_el else None
                        away_team = away_team_el.inner_text().strip() if away_team_el else None

                        if not home_team or not away_team:
                            continue

                        home_starter_text = home_pitcher_el.inner_text().strip() if home_pitcher_el else None
                        away_starter_text = away_pitcher_el.inner_text().strip() if away_pitcher_el else None

                        # "미정" 또는 빈 문자열이면 None 처리
                        home_starter = home_starter_text if home_starter_text and home_starter_text not in ("미정", "-", "") else None
                        away_starter = away_starter_text if away_starter_text and away_starter_text not in ("미정", "-", "") else None

                        games.append({
                            "game_date": date_str,
                            "home_team": home_team,
                            "away_team": away_team,
                            "home_starter": home_starter,
                            "away_starter": away_starter,
                            "game_time": time_el.inner_text().strip() if time_el else None,
                            "venue": venue_el.inner_text().strip() if venue_el else None,
                        })
                    except Exception as e:
                        logger.warning(f"네이버 경기 파싱 오류: {e}")
                        continue

                browser.close()

        except Exception as e:
            logger.error(f"네이버 크롤링 실패: {e}")

        logger.info(f"네이버 {date_str}: {len(games)}경기 수집")
        return games

    def fetch_game_result(self, game_id: str) -> Optional[dict]:
        """
        특정 경기 결과 수집.

        Returns:
            {
                "home_score": 5,
                "away_score": 3,
                "status": "COMPLETED",
            }
        """
        url = f"{NAVER_SPORTS_BASE}/kbaseball/gameCenter/gameResult.nhn?gameId={game_id}"

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=20000)

                home_score_el = page.query_selector("[class*='home_team'] [class*='score']")
                away_score_el = page.query_selector("[class*='away_team'] [class*='score']")

                result = {
                    "home_score": int(home_score_el.inner_text().strip()) if home_score_el else None,
                    "away_score": int(away_score_el.inner_text().strip()) if away_score_el else None,
                    "status": "COMPLETED",
                }
                browser.close()
                return result

        except Exception as e:
            logger.error(f"경기 결과 수집 실패 (game_id={game_id}): {e}")
            return None
