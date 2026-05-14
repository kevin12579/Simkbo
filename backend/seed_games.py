"""
KBO 경기 결과 시드 스크립트.
games 테이블이 비어 있을 때 1회 실행하여 2023~2025 경기 데이터를 수집합니다.

실행:
    cd backend
    venv/Scripts/python seed_games.py
    venv/Scripts/python seed_games.py --seasons 2024 2025
    venv/Scripts/python seed_games.py --seasons 2025 --months 3 4 5
"""
import argparse
import sys
from playwright.sync_api import sync_playwright
from app.db.database import SessionLocal
from app.crawler.kbo_official_crawler import KBOOfficialCrawler

KBO_SEASON_MONTHS = list(range(3, 11))  # 3월~10월


def seed(seasons: list[int], months: list[int]):
    """브라우저 인스턴스 1개를 재사용하여 전체 데이터 수집."""
    db = SessionLocal()
    crawler = KBOOfficialCrawler()
    total = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for year in seasons:
                year_total = 0
                for month in months:
                    print(f"  {year}/{month:02d} 수집 중...", end=" ", flush=True)
                    count = crawler.save_games_with_browser(year, month, db, browser)
                    print(f"{count}경기 저장")
                    year_total += count

                print(f"[{year}] 합계: {year_total}경기")
                total += year_total

            browser.close()
    finally:
        db.close()

    print(f"\n완료: 총 {total}경기 저장")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KBO 경기 데이터 시드")
    parser.add_argument(
        "--seasons", nargs="+", type=int,
        default=[2023, 2024, 2025],
        help="수집할 시즌 (기본: 2023 2024 2025)",
    )
    parser.add_argument(
        "--months", nargs="+", type=int,
        default=KBO_SEASON_MONTHS,
        help="수집할 월 (기본: 3~10)",
    )
    args = parser.parse_args()

    print(f"시즌: {args.seasons}, 월: {args.months}")
    total = seed(args.seasons, args.months)
    sys.exit(0 if total > 0 else 1)
