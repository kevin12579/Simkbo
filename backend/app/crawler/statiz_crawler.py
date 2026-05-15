"""
statiz.co.kr에서 선수 시즌 통계 수집.

로그인 방식: Playwright 퍼시스턴트 컨텍스트 (쿠키 영구 저장)
수집 데이터:
  - 투수 시즌 통계: ERA, WHIP, FIP, 이닝, 삼진, 볼넷, WAR
  - 타자 시즌 통계: AVG, OBP, SLG, OPS, HR, RBI, WAR

주의사항:
  - 요청 간 반드시 2.5초 이상 딜레이
  - player_ids.json 캐시로 중복 검색 방지
  - 최초 실행 시 브라우저에서 수동 로그인 필요 (이후 쿠키 재사용)
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.crawler.base_crawler import BaseCrawler
from app.utils.logger import logger

STATIZ_BASE = "https://www.statiz.co.kr"
CACHE_FILE = Path("data/cache/player_ids.json")
USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_profile")


class StatizCrawler(BaseCrawler):

    def __init__(self, delay: float = 7.0):
        super().__init__(delay=delay)
        self._player_id_cache: dict = {}
        self._load_cache()

    def _load_cache(self):
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                self._player_id_cache = json.load(f)
            logger.info(f"Statiz 플레이어 캐시 로드: {len(self._player_id_cache)}명")

    def _save_cache(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._player_id_cache, f, ensure_ascii=False, indent=2)

    def _run_with_playwright(self, url: str) -> Optional[str]:
        """
        Playwright 퍼시스턴트 컨텍스트로 페이지 HTML 반환.
        최초 실행 시 브라우저에서 수동 로그인 필요.
        """
        html_content = ""
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = context.pages[0]
            try:
                page.goto(STATIZ_BASE, wait_until="domcontentloaded")
                time.sleep(self.delay)  # 홈 페이지 로드 후 대기

                # 로그인 여부 확인
                if page.locator("text=로그인").count() > 0:
                    print("\n[최초 1회 로그인 필요]")
                    print("열려있는 브라우저 창에서 스탯티즈 로그인을 직접 진행해 주세요!")
                    print("로그인 완료 후 [Enter] 키를 누르면 크롤링이 재개됩니다...")
                    input()

                page.goto(url, wait_until="domcontentloaded")
                time.sleep(self.delay)  # 선수 페이지 로드 후 대기
                page.wait_for_selector("table", timeout=15000)
                html_content = page.content()

            except Exception as e:
                logger.error(f"Playwright 오류: {e}")
                return None
            finally:
                context.close()

        return html_content

    def search_player(self, name: str) -> Optional[str]:
        """
        선수 이름으로 Statiz player_no 검색.
        캐시에 있으면 캐시에서 반환.

        Returns: player_no (예: "13061") or None
        """
        if name in self._player_id_cache:
            return self._player_id_cache[name]

        search_url = f"{STATIZ_BASE}/player/?m=search&name={name}"
        html = self._run_with_playwright(search_url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        player_link = soup.select_one("table tbody tr a[href*='p_no']")
        if not player_link:
            return None

        href = player_link.get("href", "")
        match = re.search(r"p_no=(\d+)", href)
        if match:
            player_no = match.group(1)
            self._player_id_cache[name] = player_no
            self._save_cache()
            return player_no

        return None

    def fetch_pitcher_season_stats(self, player_no: str, season: int) -> Optional[dict]:
        """
        투수 시즌 통계 수집.

        Returns:
            {era, whip, fip, innings_pitched, strikeouts, walks, war_pitcher}
        """
        url = f"{STATIZ_BASE}/player/?m=playerinfo&p_no={player_no}&so={season}"
        logger.info(f"Statiz 투수 통계 요청: player_no={player_no}, season={season}")

        html = self._run_with_playwright(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return None

        target_table = tables[0]
        for row in target_table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in row.select("td")]
            if len(cells) < 38:
                continue

            if str(season) in cells[1]:
                try:
                    return {
                        "innings_pitched": float(cells[15]) if cells[15] else 0.0,
                        "walks": int(cells[24]) if cells[24] else 0,
                        "strikeouts": int(cells[27]) if cells[27] else 0,
                        "era": float(cells[31]) if cells[31] else 4.50,
                        "fip": float(cells[32]) if cells[32] else 4.50,
                        "whip": float(cells[36]) if cells[36] else 1.30,
                        "war_pitcher": float(cells[37]) if cells[37] else 0.0,
                    }
                except (ValueError, IndexError) as e:
                    logger.warning(f"투수 스탯 파싱 오류: {e}")
                    continue

        logger.warning(f"player_no={player_no} {season}시즌 기록 없음")
        return None

    def sync_all_pitchers(self, db, season: int) -> int:
        """
        roster.py에 정의된 모든 투수의 시즌 통계를 수집하여 DB에 저장.
        statiz_id가 None이면 건너뜀.
        """
        from app.crawler.roster import get_all_pitchers
        from app.models.db.player import Player
        from app.models.db.team import Team
        from app.models.db.player_season_stats import PlayerSeasonStats

        pitchers = get_all_pitchers()
        saved_count = 0

        for pitcher_info in pitchers:
            name = pitcher_info["name"]

            player_no = pitcher_info.get("statiz_id")
            if not player_no:
                logger.warning(f"{name}: statiz_id 미설정 — roster.py에 p_no 입력 필요")
                continue

            stats = self.fetch_pitcher_season_stats(str(player_no), season)
            if not stats:
                logger.warning(f"{name}: {season}시즌 통계 없음")
                continue

            team = db.query(Team).filter_by(short_name=pitcher_info["team_short_name"]).first()
            if not team:
                continue

            player = db.query(Player).filter_by(name=name, team_id=team.id).first()
            if not player:
                player = Player(
                    name=name,
                    team_id=team.id,
                    position=pitcher_info["position"],
                    throw_hand=pitcher_info.get("throw_hand"),
                    is_foreign=pitcher_info.get("is_foreign", False),
                )
                db.add(player)
                db.flush()

            existing = db.query(PlayerSeasonStats).filter_by(
                player_id=player.id, season=season
            ).first()

            if existing:
                for key, value in stats.items():
                    setattr(existing, key, value)
            else:
                pss = PlayerSeasonStats(player_id=player.id, season=season, **stats)
                db.add(pss)

            saved_count += 1
            logger.info(f"{name} ({season}): ERA={stats.get('era')}, WHIP={stats.get('whip')}")

        db.commit()
        return saved_count


# 단독 테스트 실행
if __name__ == "__main__":
    crawler = StatizCrawler()
    stats = crawler.fetch_pitcher_season_stats("13061", 2024)
    if stats:
        import pprint
        pprint.pprint(stats)
