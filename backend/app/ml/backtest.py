"""
시점기반 백테스트.

"매일 그날까지의 정보만으로 그날 경기를 예측" 하는 시뮬레이션.
단순 test set 정확도가 아닌 실전과 동일한 조건으로 검증.

실행:
    cd backend
    python -m app.ml.backtest
"""
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import joblib

from app.db.database import SessionLocal
from app.models.db.game import Game
from app.ml.feature_engineering import build_features_for_game, FEATURE_COLUMNS


def time_based_backtest(
    start_date: date,
    end_date: date,
    artifact_path: str = "app/ml/artifacts/kbo_xgb_v1.pkl",
) -> dict:
    """
    시점기반 백테스트.
    각 날짜에 대해 D-1 시점 피처로 D일 경기 예측 → 실제 결과와 비교.

    백테스트 결과가 65%를 초과하면 look-ahead bias 의심 (feature_engineering.py 재점검).
    """
    print(f"백테스트 기간: {start_date} ~ {end_date}")

    artifact = joblib.load(artifact_path)
    model = artifact["model"]
    calibrator = artifact.get("calibrator")

    db = SessionLocal()
    results = []

    try:
        current = start_date
        while current <= end_date:
            games = (
                db.query(Game)
                .filter(
                    Game.scheduled_at >= current,
                    Game.scheduled_at < current + timedelta(days=1),
                    Game.status == "COMPLETED",
                )
                .all()
            )

            for g in games:
                try:
                    X = build_features_for_game(
                        g.id,
                        as_of_date=current - timedelta(days=1),
                        db=db,
                    )

                    features = artifact.get("features", FEATURE_COLUMNS)
                    raw_proba = model.predict_proba(X[features])[0, 1]
                    pred_proba = calibrator.predict([raw_proba])[0] if calibrator else raw_proba

                    actual = 1 if (g.home_score is not None and g.home_score > g.away_score) else 0
                    dist = abs(pred_proba - 0.5)
                    confidence = "HIGH" if dist > 0.15 else "MEDIUM" if dist > 0.08 else "LOW"

                    results.append({
                        "date": current,
                        "game_id": g.id,
                        "predicted_home_prob": pred_proba,
                        "predicted": int(pred_proba > 0.5),
                        "actual": actual,
                        "correct": int(pred_proba > 0.5) == actual,
                        "confidence": confidence,
                    })

                except Exception:
                    pass

            current += timedelta(days=1)

    finally:
        db.close()

    df = pd.DataFrame(results)

    if df.empty:
        print("백테스트 데이터 없음")
        return {}

    report = {
        "total_games": len(df),
        "overall_accuracy": float(df["correct"].mean()),
        "high_conf_count": int((df["confidence"] == "HIGH").sum()),
        "high_conf_accuracy": (
            float(df[df["confidence"] == "HIGH"]["correct"].mean())
            if (df["confidence"] == "HIGH").any() else None
        ),
        "medium_conf_accuracy": (
            float(df[df["confidence"] == "MEDIUM"]["correct"].mean())
            if (df["confidence"] == "MEDIUM").any() else None
        ),
        "low_conf_accuracy": (
            float(df[df["confidence"] == "LOW"]["correct"].mean())
            if (df["confidence"] == "LOW").any() else None
        ),
    }

    print(f"\n백테스트 결과:")
    print(f"  전체 경기: {report['total_games']}")
    print(f"  전체 정확도: {report['overall_accuracy']:.4f} ({report['overall_accuracy']*100:.1f}%)")
    print(f"  HIGH 신뢰도 정확도: {report.get('high_conf_accuracy', 'N/A')}")
    print(f"  MEDIUM 신뢰도 정확도: {report.get('medium_conf_accuracy', 'N/A')}")

    if report["overall_accuracy"] > 0.65:
        print("\n경고: 백테스트 정확도가 65% 초과 — look-ahead bias 의심!")
        print("  as_of_date가 올바르게 적용되었는지 feature_engineering.py를 재확인하세요.")

    return report


if __name__ == "__main__":
    result = time_based_backtest(
        start_date=date(2025, 4, 1),
        end_date=date(2025, 5, 12),
    )
