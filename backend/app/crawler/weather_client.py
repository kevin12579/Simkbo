"""
기상청 Open API — 단기예보 조회.

API 신청: https://www.data.go.kr → "기상청_단기예보_조회서비스"
무료 1,000회/일 제공.

야외 구장만 날씨 적용 (고척스카이돔은 실내이므로 제외):
  - 잠실, 수원KT, 인천SSG, 창원NC, 광주기아, 사직, 대구삼성, 한화생명 → 날씨 영향 있음
  - 고척스카이돔 → is_dome=True, 날씨 무시
"""
from datetime import datetime
from typing import Optional

import requests

from app.config import settings
from app.utils.logger import logger

# 구장별 기상청 격자 좌표
STADIUM_COORDS = {
    "잠실야구장":              {"nx": 62,  "ny": 126},
    "수원KT위즈파크":          {"nx": 60,  "ny": 121},
    "인천SSG랜더스필드":        {"nx": 55,  "ny": 124},
    "창원NC파크":              {"nx": 90,  "ny": 91},
    "광주-기아챔피언스필드":    {"nx": 58,  "ny": 74},
    "사직야구장":              {"nx": 98,  "ny": 76},
    "대구삼성라이온즈파크":     {"nx": 89,  "ny": 90},
    "한화생명이글스파크":       {"nx": 68,  "ny": 100},
    "고척스카이돔":             None,  # 돔 구장 — 날씨 무관
}

_API_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"


def fetch_weather(stadium: str, game_datetime: datetime) -> dict:
    """
    경기 당일 날씨 조회.

    Args:
        stadium: 구장명 (STADIUM_COORDS 키)
        game_datetime: 경기 일시

    Returns:
        {
            "pop": 30,            # 강수확률 (%)
            "wind_speed": 2.5,    # 풍속 (m/s)
            "temp": 18.0,         # 기온 (°C)
            "is_dome": False,
            "is_rain_risk": False # 강수확률 30% 이상
        }
    """
    # 돔 구장
    if STADIUM_COORDS.get(stadium) is None:
        return {"pop": 0, "wind_speed": 0.0, "temp": 22.0, "is_dome": True, "is_rain_risk": False}

    if not settings.weather_api_key:
        return _default_weather()

    coords = STADIUM_COORDS.get(stadium)
    if not coords:
        return _default_weather()

    base_date = game_datetime.strftime("%Y%m%d")
    base_time = "0500"

    params = {
        "serviceKey": settings.weather_api_key,
        "pageNo": 1,
        "numOfRows": 100,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": coords["nx"],
        "ny": coords["ny"],
    }

    try:
        resp = requests.get(_API_URL, params=params, timeout=10)
        data = resp.json()
        items = data["response"]["body"]["items"]["item"]

        pop = 0
        wsd = 0.0
        tmp = 20.0

        game_hour = game_datetime.strftime("%H00")
        for item in items:
            if item["fcstTime"] == game_hour:
                category = item["category"]
                value = item["fcstValue"]
                if category == "POP":
                    pop = int(value)
                elif category == "WSD":
                    wsd = float(value)
                elif category == "TMP":
                    tmp = float(value)

        return {
            "pop": pop,
            "wind_speed": wsd,
            "temp": tmp,
            "is_dome": False,
            "is_rain_risk": pop >= 30,
        }

    except Exception as e:
        logger.error(f"기상청 API 오류 ({stadium}): {e}")
        return _default_weather()


def _default_weather() -> dict:
    return {"pop": 0, "wind_speed": 0.0, "temp": 20.0, "is_dome": False, "is_rain_risk": False}
