"""
Main API router for the trading bot.

This module will contain the main API endpoints for:
- Tweet data retrieval
- Trade history and positions
- Manual override controls
- Risk management
"""

from fastapi import APIRouter
from app.api.risk import router as risk_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include risk management router
api_router.include_router(risk_router)

# Placeholder for future endpoint routers
# These will be implemented in subsequent tasks:
# - tweets router (task 8)
# - trades router (task 8)
# - positions router (task 8)


@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {"status": "API ready", "version": "1.0.0"}
