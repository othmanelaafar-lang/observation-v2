from fastapi import APIRouter

from app.api.routes.domains import router as domains_router
from app.api.routes.health import router as health_router
from app.api.routes.leaderboards import router as leaderboard_router
from app.api.routes.search import router as search_router
from app.api.routes.stats import router as stats_router
from app.api.routes.talents import router as talents_router
from app.api.routes.universities import router as universities_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(talents_router, tags=["talents"])
api_router.include_router(leaderboard_router, tags=["leaderboards"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(stats_router, tags=["stats"])
api_router.include_router(domains_router, tags=["domains"])
api_router.include_router(universities_router, tags=["universities"])
