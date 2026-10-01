"""JSON API routers for SPA."""

from fastapi import APIRouter

from . import agent, calendar, events, health, intel, profile, progress, review

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(intel.router)
api_router.include_router(progress.router)
api_router.include_router(calendar.router)
api_router.include_router(events.router)
api_router.include_router(review.router)
api_router.include_router(agent.router)
api_router.include_router(profile.router)
