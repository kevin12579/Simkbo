"""
Stage 1: XGBoost 이진 분류 모델.

학습 방법:
    cd backend
    python -m app.ml.xgboost_model

목표 성능:
  - MVP: Test Accuracy >= 55%, LogLoss <= 0.69
  - 최종: Accuracy >= 58%, LogLoss <= 0.65

★★★ 절대 금지: train_test_split(shuffle=True) ★★★
  → 시간 기준 분할만 사용 (미래 경기로 과거를 예측하면 안 됨)
"""
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.isotonic import IsotonicRegression

from app.ml.feature_engineering import FEATURE_COLUMNS

ARTIFACT_DIR = Path("app/ml/artifacts")
TRAINING_DATA_PATH = Path("data/training_set.parquet")


def train_xgboost(data_path: Path = TRAINING_DATA_PATH) -> dict:
    """
    XGBoost 모델 학습 & 저장.

    시간 기준 분할:
      Train: 70% (2023 전체 + 2024 초반)
      Val:   15% (2024 후반)
      Test:  15% (2025 — 실전과 가장 유사)
    """
    print("학습 데이터 로드 중...")
    df = pd.read_parquet(data_path)

    # ★ 시간 기준 정렬 (필수!)
    df = df.sort_values("scheduled_at").reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]

    print(f"  Train: {len(train)}경기 ({train['scheduled_at'].min().date()} ~ {train['scheduled_at'].max().date()})")
    print(f"  Val:   {len(val)}경기 ({val['scheduled_at'].min().date()} ~ {val['scheduled_at'].max().date()})")
    print(f"  Test:  {len(test)}경기 ({test['scheduled_at'].min().date()} ~ {test['scheduled_at'].max().date()})")

    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        early_stopping_rounds=30,
        random_state=42,
        tree_method="hist",
        verbosity=0,
    )

    print("\nXGBoost 학습 시작...")
    model.fit(
        train[FEATURE_COLUMNS], train["label"],
        eval_set=[(val[FEATURE_COLUMNS], val["label"])],
        verbose=50,
    )

    # 평가
    test_proba = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    test_pred = (test_proba > 0.5).astype(int)

    test_acc = accuracy_score(test["label"], test_pred)
    test_logloss = log_loss(test["label"], test_proba)
    test_brier = brier_score_loss(test["label"], test_proba)

    print(f"\nTest 성능:")
    print(f"  Accuracy: {test_acc:.4f} (목표: >= 0.55)")
    print(f"  LogLoss:  {test_logloss:.4f} (목표: <= 0.69)")
    print(f"  Brier:    {test_brier:.4f}")

    # Calibration (확률 보정)
    val_proba = model.predict_proba(val[FEATURE_COLUMNS])[:, 1]
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(val_proba, val["label"])

    # Feature Importance 출력 (상위 15개)
    feature_importance = pd.Series(
        model.feature_importances_,
        index=FEATURE_COLUMNS,
    ).sort_values(ascending=False)
    print(f"\nFeature Importance Top 15:")
    print(feature_importance.head(15).to_string())

    # 모델 저장
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "features": FEATURE_COLUMNS,
        "model_name": "xgboost_v1",
        "version": "v1.0",
        "label_map": {0: "AWAY_WIN", 1: "HOME_WIN"},
        "needs_scale": False,
        "scaler": None,
        "calibrator": calibrator,
        "trained_at": datetime.now().isoformat(),
        "test_accuracy": float(test_acc),
        "test_logloss": float(test_logloss),
        "test_brier": float(test_brier),
        "train_size": len(train),
        "val_size": len(val),
        "test_size": len(test),
    }

    artifact_path = ARTIFACT_DIR / "kbo_xgb_v1.pkl"
    joblib.dump(artifact, artifact_path)
    joblib.dump(calibrator, ARTIFACT_DIR / "calibrator.pkl")

    print(f"\n모델 저장 완료: {artifact_path}")

    return {
        "accuracy": test_acc,
        "logloss": test_logloss,
        "brier": test_brier,
        "artifact_path": str(artifact_path),
    }


def load_xgboost_model(artifact_path: str = None):
    """저장된 XGBoost 아티팩트 로드. 파일 없으면 None 반환."""
    from app.config import settings
    path = artifact_path or settings.xgboost_artifact_path
    if not Path(path).exists():
        return None
    return joblib.load(path)


def predict_proba(features_df: pd.DataFrame, artifact: dict = None) -> float:
    """
    단일 경기 피처로 XGBoost 예측 확률 반환.

    Returns: 홈팀 승리 확률 (calibration 적용)
    """
    if artifact is None:
        artifact = load_xgboost_model()

    model = artifact["model"]
    calibrator = artifact.get("calibrator")

    raw_proba = model.predict_proba(features_df[FEATURE_COLUMNS])[0, 1]

    if calibrator:
        return float(calibrator.predict([raw_proba])[0])
    return float(raw_proba)


if __name__ == "__main__":
    result = train_xgboost()
    if result["accuracy"] < 0.55:
        print("경고: 목표 정확도 미달 — 피처 엔지니어링 또는 하이퍼파라미터 재검토 필요")
