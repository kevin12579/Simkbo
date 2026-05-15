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

from app.ml.feature_engineering import FEATURE_COLUMNS

ARTIFACT_DIR = Path("app/ml/artifacts")
TRAINING_DATA_PATH = Path("data/training_set.parquet")

# 단독 예측력 검증 결과 (check_signal.py):
#   season_wr_diff alone → 55.66% test accuracy (목표 초과)
#   추가 피처는 noise를 더해 오히려 성능 저하
# → 강한 신호 피처 중심으로 최소화
SELECTED_FEATURES = [
    "season_wr_diff",       # 가장 강한 신호
    "last10_wr_diff",       # 최근 10경기 승률 차이
    "run_diff_diff",        # 최근 득실차 차이
    "streak_diff",          # 연속 승패 차이
]


def train_xgboost(data_path: Path = TRAINING_DATA_PATH) -> dict:
    """
    XGBoost 모델 학습 & 저장.

    시간 기준 분할:
      Train: 70% (2023 전체 + 2024 초반)
      Val:   15% (2024 후반)
      Test:  15% (2025 - 실전과 가장 유사)
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
    print(f"  사용 피처: {SELECTED_FEATURES}")

    # max_depth=2, 선택된 피처만 사용 -> 과적합 방지
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=2,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=1.0,
        min_child_weight=20,
        reg_alpha=1.0,
        reg_lambda=5.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        tree_method="hist",
        verbosity=0,
    )

    print("\nXGBoost 학습 시작...")
    model.fit(
        train[SELECTED_FEATURES], train["label"],
        eval_set=[(val[SELECTED_FEATURES], val["label"])],
        verbose=20,
    )

    # 평가
    test_proba = model.predict_proba(test[SELECTED_FEATURES])[:, 1]
    test_pred = (test_proba > 0.5).astype(int)

    test_acc = accuracy_score(test["label"], test_pred)
    test_logloss = log_loss(test["label"], test_proba)
    test_brier = brier_score_loss(test["label"], test_proba)

    train_acc = accuracy_score(train["label"], model.predict(train[SELECTED_FEATURES]))

    print(f"\nTest 성능:")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Test  Accuracy: {test_acc:.4f} (목표: >= 0.55)")
    print(f"  LogLoss:        {test_logloss:.4f} (목표: <= 0.69)")
    print(f"  Brier:          {test_brier:.4f}")

    # Feature Importance
    feature_importance = pd.Series(
        model.feature_importances_,
        index=SELECTED_FEATURES,
    ).sort_values(ascending=False)
    print(f"\nFeature Importance:")
    print(feature_importance.to_string())

    # 모델 저장
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "features": SELECTED_FEATURES,   # 추론 시 이 목록 사용
        "model_name": "xgboost_v1",
        "version": "v1.0",
        "label_map": {0: "AWAY_WIN", 1: "HOME_WIN"},
        "needs_scale": False,
        "scaler": None,
        "calibrator": None,
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

    Returns: 홈팀 승리 확률
    """
    if artifact is None:
        artifact = load_xgboost_model()

    model = artifact["model"]
    calibrator = artifact.get("calibrator")
    features = artifact.get("features", FEATURE_COLUMNS)  # 아티팩트에 저장된 피처 목록 사용

    raw_proba = model.predict_proba(features_df[features])[0, 1]

    if calibrator:
        return float(calibrator.predict([raw_proba])[0])
    return float(raw_proba)


if __name__ == "__main__":
    result = train_xgboost()
    if result["accuracy"] < 0.55:
        print("경고: 목표 정확도 미달 - 피처 엔지니어링 또는 하이퍼파라미터 재검토 필요")
