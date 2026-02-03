"""
Main API router for the trading bot.

This module contains the main API endpoints for:
- Tweet data retrieval
- Trade history and positions
- Manual override controls
- Risk management
"""

from fastapi import APIRouter
from app.api.risk import router as risk_router
from app.api.tweets import router as tweets_router
from app.api.trades import router as trades_router
from app.api.positions import router as positions_router
from app.api.override import router as override_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all endpoint routers
api_router.include_router(risk_router)
api_router.include_router(tweets_router)
api_router.include_router(trades_router)
api_router.include_router(positions_router)
api_router.include_router(override_router)


@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {"status": "API ready", "version": "1.0.0"}
