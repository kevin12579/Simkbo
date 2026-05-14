"""
XGBoost + LSTM 앙상블.
신뢰도 기반 동적 가중치 적용.
"""


def ensemble_prediction(
    xgb_proba: float,
    lstm_proba: float,
    context: dict,
) -> dict:
    """
    두 모델의 예측을 앙상블하여 최종 확률 및 신뢰도 반환.

    Args:
        xgb_proba: XGBoost 홈팀 승리 확률 (calibration 적용 후)
        lstm_proba: LSTM 홈팀 승리 확률
        context:
            - starter_unconfirmed: bool (선발 미확정 시 True)
            - lstm_available: bool (LSTM 모델 사용 가능 여부)

    Returns:
        {
            "home_win_prob": 0.62,
            "away_win_prob": 0.38,
            "confidence_level": "HIGH",  # "HIGH" | "MEDIUM" | "LOW"
            "xgboost_home_prob": 0.61,
            "lstm_home_prob": 0.64,
            "weights": {"xgb": 0.6, "lstm": 0.4},
        }
    """
    w_xgb = 0.6
    w_lstm = 0.4

    # LSTM 모델 없으면 XGBoost만 사용
    if not context.get("lstm_available", True):
        w_xgb = 1.0
        w_lstm = 0.0

    diff = abs(xgb_proba - lstm_proba)

    # 두 모델 차이가 크면 LSTM 가중치 감소
    if diff > 0.20:
        w_xgb = 0.75
        w_lstm = 0.25

    # 선발 미확정 시 XGBoost만 사용 (팀 통계 기반 예측)
    if context.get("starter_unconfirmed"):
        w_xgb = 1.0
        w_lstm = 0.0

    final = w_xgb * xgb_proba + w_lstm * lstm_proba
    final = max(0.05, min(0.95, final))  # 극단값 방지

    # 신뢰도 산정
    distance_from_50 = abs(final - 0.5)
    agreement = 1.0 - diff
    confidence_score = distance_from_50 * agreement

    if confidence_score > 0.12:
        confidence = "HIGH"
    elif confidence_score > 0.06:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # 선발 미확정 시 최대 MEDIUM
    if context.get("starter_unconfirmed") and confidence == "HIGH":
        confidence = "MEDIUM"

    return {
        "home_win_prob": round(final, 4),
        "away_win_prob": round(1.0 - final, 4),
        "confidence_level": confidence,
        "xgboost_home_prob": round(xgb_proba, 4),
        "lstm_home_prob": round(lstm_proba, 4),
        "weights": {"xgb": w_xgb, "lstm": w_lstm},
    }
