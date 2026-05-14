import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", encoding="utf-8")


class Settings:
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://kbo_user:kbo_password@localhost:5432/kbo_predict",
    )

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Statiz credentials
    statiz_user: str = os.getenv("STATIZ_USER", "")
    statiz_pass: str = os.getenv("STATIZ_PASS", "")

    # 기상청 API
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")

    # OpenAI API
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # 앱 설정
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")

    # ML 아티팩트 경로
    xgboost_artifact_path: str = os.getenv(
        "XGBOOST_ARTIFACT_PATH", "app/ml/artifacts/kbo_xgb_v1.pkl"
    )
    lstm_artifact_path: str = os.getenv(
        "LSTM_ARTIFACT_PATH", "app/ml/artifacts/kbo_lstm_v1.pt"
    )
    calibrator_path: str = os.getenv(
        "CALIBRATOR_PATH", "app/ml/artifacts/calibrator.pkl"
    )
    model_version: str = os.getenv("MODEL_VERSION", "v1.0-xgb+lstm")


settings = Settings()
