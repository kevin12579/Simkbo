"""
Stage 2: LSTM + MLP 하이브리드 모델.

입력:
  - 시계열 (LSTM): 선발 투수 최근 5경기, 팀 최근 10경기
  - 정적 (MLP): 누적 피처 30개

목표: XGBoost와 앙상블하여 logloss 개선

주의: 샘플 수(2,160)가 적으므로 Dropout, Early Stopping 필수
"""
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

ARTIFACT_DIR = Path("app/ml/artifacts")


class KBOPredictionModel(nn.Module):
    """
    LSTM + MLP 하이브리드.

    홈/원정 선발 투수 최근 5경기(시계열) + 팀 최근 10경기(시계열) +
    정적 피처 30개를 결합하여 홈팀 승리 확률 출력.
    """

    def __init__(
        self,
        pitcher_seq_len: int = 5,
        pitcher_feat_dim: int = 5,    # ERA, WHIP, K, IP, ER
        team_seq_len: int = 10,
        team_feat_dim: int = 4,        # 득점, 실점, 승패, 홈여부
        static_dim: int = 30,
        hidden: int = 64,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.pitcher_lstm = nn.LSTM(
            input_size=pitcher_feat_dim,
            hidden_size=hidden,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
        )

        self.team_lstm = nn.LSTM(
            input_size=team_feat_dim,
            hidden_size=hidden,
            num_layers=1,
            batch_first=True,
        )

        self.static_mlp = nn.Sequential(
            nn.Linear(static_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # hidden * 5 = 홈투수 + 원정투수 + 홈팀 + 원정팀 + 정적
        self.head = nn.Sequential(
            nn.Linear(hidden * 5, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(
        self,
        home_pitcher: torch.Tensor,   # (batch, 5, 5)
        away_pitcher: torch.Tensor,   # (batch, 5, 5)
        home_team: torch.Tensor,      # (batch, 10, 4)
        away_team: torch.Tensor,      # (batch, 10, 4)
        static: torch.Tensor,         # (batch, 30)
    ) -> torch.Tensor:

        _, (h_hp, _) = self.pitcher_lstm(home_pitcher)
        _, (h_ap, _) = self.pitcher_lstm(away_pitcher)
        _, (h_ht, _) = self.team_lstm(home_team)
        _, (h_at, _) = self.team_lstm(away_team)
        h_st = self.static_mlp(static)

        combined = torch.cat([
            h_hp.squeeze(0),
            h_ap.squeeze(0),
            h_ht.squeeze(0),
            h_at.squeeze(0),
            h_st,
        ], dim=1)

        logit = self.head(combined)
        return torch.sigmoid(logit).squeeze(-1)


class KBODataset(Dataset):
    """
    PyTorch Dataset.

    data: [
        {
            "home_pitcher": np.array (5, 5),
            "away_pitcher": np.array (5, 5),
            "home_team": np.array (10, 4),
            "away_team": np.array (10, 4),
            "static": np.array (30,),
            "label": int (0 or 1),
        },
        ...
    ]
    """

    def __init__(self, data: list):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            "home_pitcher": torch.FloatTensor(item["home_pitcher"]),
            "away_pitcher": torch.FloatTensor(item["away_pitcher"]),
            "home_team":    torch.FloatTensor(item["home_team"]),
            "away_team":    torch.FloatTensor(item["away_team"]),
            "static":       torch.FloatTensor(item["static"]),
            "label":        torch.FloatTensor([item["label"]]),
        }


def train_pytorch_model(
    train_data: list,
    val_data: list,
    model_config: dict = None,
    epochs: int = 50,
    patience: int = 10,
) -> KBOPredictionModel:
    """LSTM 모델 학습."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"디바이스: {device}")

    config = model_config or {}
    model = KBOPredictionModel(**config).to(device)

    train_loader = DataLoader(KBODataset(train_data), batch_size=32, shuffle=True)
    val_loader = DataLoader(KBODataset(val_data), batch_size=32, shuffle=False)

    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.BCELoss()

    best_val_loss = float("inf")
    patience_counter = 0
    best_state = None

    print(f"LSTM 학습 시작... (최대 {epochs} 에폭)")

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            inputs = {k: v.to(device) for k, v in batch.items() if k != "label"}
            labels = batch["label"].squeeze(-1).to(device)
            pred = model(**inputs)
            loss = criterion(pred, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                inputs = {k: v.to(device) for k, v in batch.items() if k != "label"}
                labels = batch["label"].squeeze(-1).to(device)
                pred = model(**inputs)
                val_loss += criterion(pred, labels).item()

        val_loss /= len(val_loader)
        train_loss /= len(train_loader)
        scheduler.step()

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch + 1}/{epochs} — Train: {train_loss:.4f}, Val: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch + 1}")
                break

    if best_state:
        model.load_state_dict(best_state)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model_state_dict": model.state_dict(),
        "model_config": config,
        "version": "v1.0-lstm",
        "best_val_loss": best_val_loss,
    }
    torch.save(artifact, ARTIFACT_DIR / "kbo_lstm_v1.pt")
    print(f"LSTM 모델 저장: app/ml/artifacts/kbo_lstm_v1.pt")

    return model


def load_lstm_model(artifact_path: str = None) -> Optional[KBOPredictionModel]:
    """저장된 LSTM 모델 로드."""
    from app.config import settings
    path = artifact_path or settings.lstm_artifact_path

    if not Path(path).exists():
        return None

    artifact = torch.load(path, map_location="cpu")
    config = artifact.get("model_config", {})
    model = KBOPredictionModel(**config)
    model.load_state_dict(artifact["model_state_dict"])
    model.eval()
    return model


def predict_proba_lstm(
    home_pitcher: np.ndarray,
    away_pitcher: np.ndarray,
    home_team: np.ndarray,
    away_team: np.ndarray,
    static: np.ndarray,
    model: KBOPredictionModel = None,
) -> float:
    """LSTM 모델로 홈팀 승리 확률 반환."""
    if model is None:
        model = load_lstm_model()
    if model is None:
        return 0.5

    with torch.no_grad():
        prob = model(
            torch.FloatTensor(home_pitcher).unsqueeze(0),
            torch.FloatTensor(away_pitcher).unsqueeze(0),
            torch.FloatTensor(home_team).unsqueeze(0),
            torch.FloatTensor(away_team).unsqueeze(0),
            torch.FloatTensor(static).unsqueeze(0),
        )
    return float(prob.item())
