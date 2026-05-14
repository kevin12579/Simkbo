# KBO 10개 팀 주요 선발 투수 로스터 (2025 시즌 기준)
# statiz_id: statiz.co.kr에서 선수 클릭 후 URL의 p_no 값
# 예: /player/?m=playerinfo&p_no=12345 → statiz_id: 12345
# None이면 해당 선수 수집 건너뜀
#
# ⚠️ 주의 사항 (2025-05-14 기준 조사):
# - 엔스(LG): 2024 시즌 후 MLB 복귀, 2025년 KBO 없음
# - 벤자민(KT): 활약연도 2022~2024, 2025년 KT 미소속 (KT 2025 외인 투수는 쿠에바스 등)
# - 윌리엄스(KT): KBO 야구 선수로 확인 불가 (농구팀 동명이인 존재)
# - 페라자(한화): 2024 시즌 후 MLB행, 2025년 한화 미소속 (2026년 복귀)
# - 로무알도(SSG): p_no 검색 결과 없음, 수동 확인 필요
# - 뷰캐넌(삼성): p_no 검색 결과 없음, 수동 확인 필요
# → None으로 유지된 선수는 statiz.co.kr에서 직접 확인 후 입력 필요

ROSTERS = {
    "두산": [
        {"name": "곽빈",      "statiz_id": 13061,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "이영하",    "statiz_id": 12568,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "알칸타라",  "statiz_id": 13941,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
    ],
    "LG": [
        {"name": "임찬규",    "statiz_id": 10652,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
        {"name": "엔스",      "statiz_id": None,   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ 2025년 MLB 복귀, KBO 미소속
        {"name": "손주영",    "statiz_id": 12908,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "키움": [
        {"name": "하영민",    "statiz_id": 11222,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "헤이수스",  "statiz_id": 16138,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ throw_hand 확인: 실제 좌투(LEFT)
    ],
    "KT": [
        {"name": "벤자민",    "statiz_id": 15143,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ 활약연도 2022~2024, 2025년 미소속 가능성
        {"name": "고영표",    "statiz_id": 11308,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
        {"name": "윌리엄스",  "statiz_id": None,   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ KBO 야구 선수로 확인 불가
    ],
    "SSG": [
        {"name": "로무알도",  "statiz_id": None,   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ p_no 미확인
        {"name": "김광현",    "statiz_id": 10126,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
        {"name": "오원석",    "statiz_id": 14581,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
    ],
    "NC": [
        {"name": "레예스",    "statiz_id": 15861,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "류진욱",    "statiz_id": 11355,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "신민혁",    "statiz_id": 13085,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "KIA": [
        {"name": "양현종",    "statiz_id": 10058,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
        {"name": "네일",      "statiz_id": 16088,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "윤영철",    "statiz_id": 15432,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
    ],
    "롯데": [
        {"name": "반즈",      "statiz_id": 15011,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},
        {"name": "박세웅",    "statiz_id": 11357,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "나균안",    "statiz_id": 12930,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
    "삼성": [
        {"name": "원태인",    "statiz_id": 14113,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
        {"name": "뷰캐넌",    "statiz_id": None,   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ p_no 미확인
        {"name": "최채흥",    "statiz_id": 13156,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},  # ⚠️ 실제 좌투좌타
    ],
    "한화": [
        {"name": "류현진",    "statiz_id": 10590,  "position": "PITCHER", "throw_hand": "LEFT",  "is_foreign": False},
        {"name": "페라자",    "statiz_id": None,   "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": True},   # ⚠️ 2025년 MLB행, 2026년 한화 복귀
        {"name": "문동주",    "statiz_id": 15013,  "position": "PITCHER", "throw_hand": "RIGHT", "is_foreign": False},
    ],
}

# 팀명 → 구장 매핑
TEAM_STADIUMS = {
    "두산":  "잠실야구장",
    "LG":   "잠실야구장",
    "키움":  "고척스카이돔",
    "KT":   "수원KT위즈파크",
    "SSG":  "인천SSG랜더스필드",
    "NC":   "창원NC파크",
    "KIA":  "광주-기아챔피언스필드",
    "롯데":  "사직야구장",
    "삼성":  "대구삼성라이온즈파크",
    "한화":  "한화생명이글스파크",
}

# 팀 전체 이름 매핑
TEAM_FULL_NAMES = {
    "두산":  "두산 베어스",
    "LG":   "LG 트윈스",
    "키움":  "키움 히어로즈",
    "KT":   "KT 위즈",
    "SSG":  "SSG 랜더스",
    "NC":   "NC 다이노스",
    "KIA":  "KIA 타이거즈",
    "롯데":  "롯데 자이언츠",
    "삼성":  "삼성 라이온즈",
    "한화":  "한화 이글스",
}


def get_all_pitchers() -> list[dict]:
    result = []
    for team_name, players in ROSTERS.items():
        for p in players:
            result.append({**p, "team_short_name": team_name})
    return result


def get_all_teams() -> list[dict]:
    return [
        {
            "short_name": short_name,
            "full_name": TEAM_FULL_NAMES[short_name],
            "stadium": TEAM_STADIUMS[short_name],
            "is_dome": TEAM_STADIUMS[short_name] == "고척스카이돔",
        }
        for short_name in ROSTERS
    ]