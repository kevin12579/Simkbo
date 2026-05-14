"""
KBO 공식 사이트에서 팀 순위 스냅샷 및 경기 일정 수집.

핵심 기능:
  - fetch_team_rank_daily(date): 특정 날짜의 팀 순위 스냅샷 (시점 백테스트 핵심)
  - fetch_schedule(year, month): 월별 경기 일정
  - bulk_collect_snapshots: 날짜 범위 전체 수집 (학습 데이터 구축)

왜 이 크롤러가 중요한가:
  - 과거 임의 날짜의 팀 순위를 조회할 수 있어 look-ahead bias 없는 학습 데이터 생성 가능
"""
import re
from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.crawler.base_crawler import BaseCrawler
from app.utils.logger import logger


class KBOOfficialCrawler(BaseCrawler):
    BASE_URL = "https://www.koreabaseball.com"

    def fetch_team_rank_daily(self, date_str: str) -> list[dict]:
        """
        date_str: 'YYYYMMDD' 형식 (예: '20240501')
        해당 시점의 KBO 팀 순위표를 크롤링합니다.
        """
        url = f"{self.BASE_URL}/Record/TeamRank/TeamRankDaily.aspx?seriesId=0&date={date_str}"
        logger.info(f"[{date_str}] KBO 팀 순위 요청: {url}")

        resp = self.safe_get(url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.tData")
        if not table:
            logger.warning(f"[{date_str}] 순위 테이블 없음")
            return []

        rows = []
        for tr in table.select("tbody tr"):
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if len(cells) < 10:
                continue

            try:
                # 컬럼 순서: 순위|팀명|경기|승|패|무|승률|게임차|최근10경기|연속|홈|원정
                last10 = cells[8]  # 예: "5승1무4패"
                wins_match = re.search(r"(\d+)승", last10)
                last10_wins = int(wins_match.group(1)) if wins_match else 0
                losses_match = re.search(r"(\d+)패", last10)
                last10_losses = int(losses_match.group(1)) if losses_match else 0

                streak = cells[9]  # 예: "3연승", "2연패"
                streak_type = "WIN" if "승" in streak else "LOSS" if "패" in streak else "DRAW"
                streak_match = re.search(r"(\d+)", streak)
                streak_count = int(streak_match.group(1)) if streak_match else 0

                rows.append({
                    "snapshot_date": date_str,
                    "rank": int(cells[0]),
                    "team_name": cells[1],
                    "games_played": int(cells[2]),
                    "wins": int(cells[3]),
                    "losses": int(cells[4]),
                    "draws": int(cells[5]),
                    "season_win_rate": float(cells[6]),
                    "last10_wins": last10_wins,
                    "last10_losses": last10_losses,
                    "streak_type": streak_type,
                    "streak_count": streak_count,
                })
            except (ValueError, IndexError) as e:
                logger.debug(f"파싱 오류 ({cells}): {e}")
                continue

        return rows

    def save_team_snapshots(self, date_str: str, db: Session) -> int:
        """
        특정 날짜의 팀 순위를 team_daily_snapshots 테이블에 저장 (UPSERT).
        """
        from app.models.db.team import Team
        from app.models.db.team_snapshot import TeamDailySnapshot

        snapshot_date = datetime.strptime(date_str, "%Y%m%d").date()
        rows = self.fetch_team_rank_daily(date_str)
        if not rows:
            return 0

        teams = {t.short_name: t.id for t in db.query(Team).all()}
        saved_count = 0

        for row in rows:
            team_id = teams.get(row["team_name"])
            if not team_id:
                logger.warning(f"팀 없음: {row['team_name']}")
                continue

            existing = db.query(TeamDailySnapshot).filter_by(
                team_id=team_id, snapshot_date=snapshot_date
            ).first()

            if existing:
                for key, value in row.items():
                    if key not in ("team_name", "snapshot_date"):
                        setattr(existing, key, value)
            else:
                snapshot = TeamDailySnapshot(
                    team_id=team_id,
                    snapshot_date=snapshot_date,
                    **{k: v for k, v in row.items() if k not in ("team_name", "snapshot_date")},
                )
                db.add(snapshot)

            saved_count += 1

        db.commit()
        return saved_count

    def fetch_schedule(self, year: int, month: int) -> list[dict]:
        """
        Playwright로 KBO 공식 사이트 월별 경기 일정 및 결과 수집.
        드롭다운을 직접 조작하여 원하는 연도/월 데이터를 가져옵니다.

        Returns: list of {date, time, away_team, home_team,
                           away_score, home_score, stadium, status}
        """
        from playwright.sync_api import sync_playwright

        base_url = f"{self.BASE_URL}/Schedule/Schedule.aspx"
        month_str = f"{month:02d}"

        captured: list = []

        def _on_response(resp):
            if "GetScheduleList" in resp.url:
                try:
                    data = resp.json()
                    rows = data.get("rows", [])
                    if rows:
                        captured.append(rows)
                except Exception:
                    pass

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("response", _on_response)

                # 초기 페이지 로드
                page.goto(base_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)

                # 드롭다운이 렌더링될 때까지 대기
                page.wait_for_selector("#ddlYear", timeout=10000)
                page.wait_for_selector("#ddlMonth", timeout=10000)

                # 연도 선택
                page.select_option("#ddlYear", str(year))
                page.wait_for_timeout(500)

                # 시리즈 정규시즌 선택
                page.select_option("#ddlSeries", "0,9,6")
                page.wait_for_timeout(500)

                # 월 선택 후 change 이벤트 트리거
                captured.clear()
                page.select_option("#ddlMonth", month_str)
                page.wait_for_timeout(3000)

                # 데이터가 아직 없으면 검색 버튼 클릭 시도
                if not captured:
                    btn = page.query_selector("#btnSearch, .btn_search, [id*='Search']")
                    if btn:
                        btn.click()
                        page.wait_for_timeout(3000)

                browser.close()
        except Exception as e:
            logger.error(f"{year}/{month:02d} Playwright 오류: {e}")
            return []

        if not captured:
            logger.warning(f"{year}/{month:02d} 일정 데이터 없음")
            return []

        rows = captured[-1]
        return self._parse_schedule_rows(rows, year, month)

    def _parse_schedule_rows(self, rows: list, year: int, month: int) -> list[dict]:
        """
        GetScheduleList API JSON 응답을 파싱.

        각 row의 cells:
          [0] date (Class="day", RowSpan N)
          [1] time (Class="time")
          [2] play (Class="play") — HTML: <span>Away</span><em><span>Score</span>vs<span>Score</span></em><span>Home</span>
          [3] relay link
          [4] highlight link
          [5] TV
          [6] (unused)
          [7] stadium
          [8] (unused)
        """
        games = []
        current_date = None

        for row_obj in rows:
            cells = row_obj.get("row", [])
            if not cells:
                continue

            # 날짜 셀 업데이트 (RowSpan 때문에 매 row에 없을 수 있음)
            for cell in cells:
                if cell.get("Class") == "day":
                    raw = re.sub(r"<[^>]+>", "", cell.get("Text", "")).strip()
                    m = re.match(r"(\d{2})\.(\d{2})", raw)
                    if m:
                        current_date = f"{year}{m.group(1)}{m.group(2)}"
                    break

            # play 셀 찾기
            play_cell = next((c for c in cells if c.get("Class") == "play"), None)
            time_cell = next((c for c in cells if c.get("Class") == "time"), None)

            if not play_cell or not current_date:
                continue

            play_html = play_cell.get("Text", "")

            # 팀명 파싱: <span>팀A</span> ... <span>팀B</span>
            team_spans = re.findall(r"<span>([^<]+)</span>", play_html)
            if len(team_spans) < 2:
                continue
            away_team = team_spans[0].strip()
            home_team = team_spans[-1].strip()

            # 스코어 파싱: <span class="lose/win">숫자</span>
            score_spans = re.findall(r'<span class="(?:lose|win)">(\d+)</span>', play_html)

            away_score = home_score = None
            status = "SCHEDULED"

            if len(score_spans) == 2:
                away_score = int(score_spans[0])
                home_score = int(score_spans[1])
                status = "COMPLETED"
            elif "취소" in play_html or "우천" in play_html:
                status = "POSTPONED"

            # 시간 파싱
            time_str = None
            if time_cell:
                time_raw = re.sub(r"<[^>]+>", "", time_cell.get("Text", "")).strip()
                if re.match(r"\d{2}:\d{2}", time_raw):
                    time_str = time_raw

            # 구장 (index 7)
            stadium = None
            if len(cells) > 7:
                stadium = re.sub(r"<[^>]+>", "", cells[7].get("Text", "")).strip() or None

            if not away_team or not home_team:
                continue

            games.append({
                "date": current_date,
                "time": time_str,
                "away_team": away_team,
                "home_team": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "stadium": stadium,
                "status": status,
            })

        logger.info(f"{year}/{month:02d}: {len(games)}경기 파싱")
        return games

    def _fetch_schedule_with_browser(self, year: int, month: int, browser) -> list[dict]:
        """save_games_with_browser에서 사용하는 내부 메서드 (브라우저 재사용)."""
        month_str = f"{month:02d}"
        captured: list = []

        def _on_response(resp):
            if "GetScheduleList" in resp.url:
                try:
                    data = resp.json()
                    rows = data.get("rows", [])
                    if rows:
                        captured.append(rows)
                except Exception:
                    pass

        page = browser.new_page()
        try:
            page.on("response", _on_response)
            page.goto(f"{self.BASE_URL}/Schedule/Schedule.aspx", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            page.wait_for_selector("#ddlYear", timeout=10000)
            page.select_option("#ddlYear", str(year))
            page.wait_for_timeout(300)
            page.select_option("#ddlSeries", "0,9,6")
            page.wait_for_timeout(300)
            captured.clear()
            page.select_option("#ddlMonth", month_str)
            page.wait_for_timeout(3000)
            if not captured:
                btn = page.query_selector("#btnSearch, .btn_search, [id*='Search']")
                if btn:
                    btn.click()
                    page.wait_for_timeout(3000)
        except Exception as e:
            logger.error(f"{year}/{month:02d} Playwright 오류: {e}")
        finally:
            page.close()

        if not captured:
            logger.warning(f"{year}/{month:02d} 일정 데이터 없음")
            return []
        return self._parse_schedule_rows(captured[-1], year, month)

    def save_games_with_browser(self, year: int, month: int, db: Session, browser) -> int:
        """외부에서 전달받은 Playwright browser를 재사용하여 경기 저장."""
        games_data = self._fetch_schedule_with_browser(year, month, browser)
        return self._upsert_games(year, games_data, db)

    def save_games(self, year: int, month: int, db: Session) -> int:
        """
        월별 경기 일정을 games 테이블에 UPSERT (중복 방지).
        Returns: 저장된 경기 수
        """
        games_data = self.fetch_schedule(year, month)
        return self._upsert_games(year, games_data, db)

    def _upsert_games(self, year: int, games_data: list, db: Session) -> int:
        """games_data 리스트를 DB에 UPSERT. 중복은 스코어만 업데이트."""
        from datetime import datetime
        from app.models.db.team import Team
        from app.models.db.game import Game

        if not games_data:
            return 0

        teams = {t.short_name: t.id for t in db.query(Team).all()}
        saved = 0

        for g in games_data:
            home_id = teams.get(g["home_team"])
            away_id = teams.get(g["away_team"])
            if not home_id or not away_id:
                logger.warning(f"팀 미등록: {g['away_team']} vs {g['home_team']}")
                continue

            try:
                game_time = g["time"] or "18:30"
                scheduled_str = f"{g['date']} {game_time}"
                scheduled_at = datetime.strptime(scheduled_str, "%Y%m%d %H:%M")
            except ValueError:
                logger.debug(f"날짜 파싱 실패: {g}")
                continue

            # 중복 확인: 같은 날짜 + 홈/원정팀 조합
            existing = (
                db.query(Game)
                .filter(
                    Game.season == year,
                    Game.home_team_id == home_id,
                    Game.away_team_id == away_id,
                    Game.scheduled_at == scheduled_at,
                )
                .first()
            )

            if existing:
                # 결과만 업데이트
                if g["status"] == "COMPLETED":
                    existing.home_score = g["home_score"]
                    existing.away_score = g["away_score"]
                    existing.status = "COMPLETED"
            else:
                game = Game(
                    season=year,
                    scheduled_at=scheduled_at,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    home_score=g["home_score"],
                    away_score=g["away_score"],
                    status=g["status"],
                    stadium=g["stadium"],
                )
                db.add(game)

            saved += 1

        db.commit()
        return saved

    def bulk_collect_snapshots(
        self,
        start_date: str,
        end_date: str,
        db: Session,
    ) -> dict:
        """
        날짜 범위의 모든 팀 순위 스냅샷 수집.
        학습 데이터 구축 시 1회 실행.

        start_date, end_date: 'YYYYMMDD' 형식
        """
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")

        total_saved = 0
        current = start

        while current <= end:
            date_str = current.strftime("%Y%m%d")
            try:
                count = self.save_team_snapshots(date_str, db)
                total_saved += count
                logger.info(f"{date_str}: {count}개 저장")
            except Exception as e:
                logger.error(f"{date_str}: 실패 — {e}")

            current += timedelta(days=1)

        return {"total_saved": total_saved}


# 단독 테스트
if __name__ == "__main__":
    crawler = KBOOfficialCrawler()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    results = crawler.fetch_team_rank_daily(yesterday)
    if results:
        import pprint
        print(f"총 {len(results)}개 팀 데이터 수집")
        pprint.pprint(results[:2])
    else:
        print("데이터를 가져오지 못했습니다.")
