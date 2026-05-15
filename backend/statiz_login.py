"""Statiz 자동 로그인 후 세션 저장."""
import os
import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_profile")
STATIZ_BASE = "https://www.statiz.co.kr"

from app.config import settings

print(f"Statiz 자동 로그인 시작: {settings.statiz_user}")

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

    print("statiz.co.kr 접속 중...")
    page.goto(STATIZ_BASE, wait_until="domcontentloaded")
    time.sleep(2)

    # 이미 로그인된 경우 체크
    if page.locator("text=로그인").count() == 0:
        print("이미 로그인된 상태입니다.")
        context.close()
        exit(0)

    print("로그인 페이지로 이동...")
    # 로그인 링크 클릭 또는 직접 이동
    try:
        page.click("a:has-text('로그인')", timeout=5000)
        time.sleep(2)
    except Exception:
        page.goto(f"{STATIZ_BASE}/user/?m=login", wait_until="domcontentloaded")
        time.sleep(2)

    print(f"현재 URL: {page.url}")

    # 이메일 입력
    for selector in ["input[name='id']", "input[type='email']", "#id", "#email", "input[placeholder*='이메일']", "input[placeholder*='아이디']"]:
        try:
            page.fill(selector, settings.statiz_user, timeout=3000)
            print(f"이메일 입력 완료 ({selector})")
            break
        except Exception:
            continue

    # 비밀번호 입력
    for selector in ["input[name='pw']", "input[type='password']", "#pw", "#password"]:
        try:
            page.fill(selector, settings.statiz_pass, timeout=3000)
            print(f"비밀번호 입력 완료 ({selector})")
            break
        except Exception:
            continue

    # 로그인 버튼 클릭
    for selector in ["button[type='submit']", "input[type='submit']", "button:has-text('로그인')", ".btn_login"]:
        try:
            page.click(selector, timeout=3000)
            print(f"로그인 버튼 클릭 ({selector})")
            break
        except Exception:
            continue

    time.sleep(3)
    print(f"로그인 후 URL: {page.url}")

    # 로그인 성공 확인
    if page.locator("text=로그아웃").count() > 0 or page.locator("text=로그인").count() == 0:
        print("로그인 성공! 세션 저장됨.")
    else:
        print("로그인 실패 - 수동으로 로그인해 주세요.")
        print("브라우저에서 직접 로그인 후 Enter를 눌러주세요...")
        input()

    context.close()

print("완료.")
