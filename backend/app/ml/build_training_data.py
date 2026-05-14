"""
학습 데이터셋 빌드 스크립트.
완료된 모든 경기에 대해 피처(47개) + 레이블(홈승=1, 원정승=0) 생성.

실행 방법:
    cd backend
    python -m app.ml.build_training_data

예상 실행 시간: 3시즌 × 720경기 = 2,160경기 × 피처 계산 ≈ 30분~1시간
"""
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from app.db.database import SessionLocal
from app.models.db.game import Game
from app.ml.feature_engineering import build_features_for_game

OUTPUT_PATH = Path("data/training_set.parquet")


def build_training_dataset(
    seasons: list = None,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """
    모든 완료 경기에 대해 피처 + 레이블 생성.

    주의: as_of_date = 경기일 - 1일 (look-ahead bias 방지)
    """
    if seasons is None:
        seasons = [2023, 2024, 2025]

    db = SessionLocal()
    rows = []
    failed = 0

    try:
        games = (
            db.query(Game)
            .filter(
                Game.season.in_(seasons),
                Game.status == "COMPLETED",
            )
            .order_by(Game.scheduled_at)
            .all()
        )

        print(f"총 {len(games)}경기 피처 생성 시작...")

        for game in tqdm(games, desc="피처 생성"):
            try:
                # ★ 핵심: 경기일 전날까지의 정보만 사용 (look-ahead bias 방지)
                as_of = game.scheduled_at.date() - timedelta(days=1)

                features = build_features_for_game(game.id, as_of_date=as_of, db=db)

                # 레이블: 홈팀 승리 = 1, 원정팀 승리 = 0
                label = 1 if (game.home_score is not None and game.home_score > game.away_score) else 0
                features["label"] = label
                features["game_id"] = game.id
                features["scheduled_at"] = game.scheduled_at
                features["season"] = game.season

                rows.append(features)

            except Exception as e:
                failed += 1

        if not rows:
            print("생성된 피처가 없습니다. DB에 경기 데이터가 있는지 확인하세요.")
            return pd.DataFrame()

        df = pd.concat(rows, ignore_index=True)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path)

        print(f"\n학습 데이터 생성 완료!")
        print(f"  총 경기: {len(games)}")
        print(f"  성공: {len(df)}")
        print(f"  실패: {failed}")
        print(f"  홈팀 승률: {df['label'].mean():.3f} (0.5에 가까울수록 편향 없음)")
        print(f"  저장: {output_path}")

        return df

    finally:
        db.close()


if __name__ == "__main__":
    build_training_dataset()
