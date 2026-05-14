from fastapi import APIRouter

from app.api.v1 import admin, games, pitchers, teams

api_router = APIRouter()

api_router.include_router(games.router)
api_router.include_router(teams.router)
api_router.include_router(pitchers.router)
api_router.include_router(admin.router)
