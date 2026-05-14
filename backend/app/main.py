from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.db.database import Base, engine
import app.models.db  # noqa: F401 — 모든 모델을 Base에 등록


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    Base.metadata.create_all(bind=engine)
    from app.scheduler.tasks import start_scheduler
    start_scheduler()
    yield
    # 종료 시
    from app.scheduler.tasks import stop_scheduler
    stop_scheduler()


app = FastAPI(
    title="KBO 야구 승부예측 AI API",
    description="XGBoost + LSTM 앙상블 모델로 KBO 경기를 예측하는 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "KBO Predict API", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "서버 내부 오류가 발생했습니다.", "status": 500}},
    )
