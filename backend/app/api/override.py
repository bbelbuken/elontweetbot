"""
Manual override API endpoints for trading controls.

This module provides endpoints for:
- Manual trading override toggle
- Override status monitoring
- Trading control management
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict

from app.database import get_db
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/override", tags=["override"])


class OverrideToggleRequest(BaseModel):
    """Request model for override toggle."""
    enabled: bool
    reason: str = "Manual toggle"


class OverrideStatusResponse(BaseModel):
    """Response model for override status."""
    manual_override: bool
    last_updated: str
    reason: str


# In-memory storage for override state (in production, this would be in Redis or database)
_override_state = {
    "enabled": settings.trading.manual_override,
    "last_updated": None,
    "reason": "Initial configuration"
}


@router.get("/status", response_model=dict)
async def get_override_status():
    """
    Get current manual override status.

    This endpoint returns the current state of the manual trading override,
    which determines whether trades require manual approval before execution.

    Returns:
        Dictionary containing override status and metadata
    """
    try:
        logger.info("Fetching override status")

        status = {
            "manual_override": _override_state["enabled"],
            "last_updated": _override_state["last_updated"],
            "reason": _override_state["reason"],
            "config_default": settings.trading.manual_override
        }

        logger.info("Successfully retrieved override status", status=status)
        return status

    except Exception as e:
        logger.error("Failed to retrieve override status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve override status"
        )


@router.post("/toggle", response_model=dict)
async def toggle_manual_override(
    request: OverrideToggleRequest
):
    """
    Toggle manual trading override on or off.

    This endpoint allows enabling or disabling manual override mode,
    which controls whether trades are executed automatically or require approval.

    Args:
        request: Override toggle request with enabled status and reason

    Returns:
        Updated override status

    Raises:
        HTTPException: If toggle operation fails
    """
    try:
        logger.info("Toggling manual override",
                    enabled=request.enabled,
                    reason=request.reason)

        # Update override state
        _override_state["enabled"] = request.enabled
        _override_state["last_updated"] = str(datetime.utcnow().isoformat())
        _override_state["reason"] = request.reason

        # Update global settings (this affects the trading workers)
        settings.trading.manual_override = request.enabled

        status = {
            "manual_override": _override_state["enabled"],
            "last_updated": _override_state["last_updated"],
            "reason": _override_state["reason"],
            "message": f"Manual override {'enabled' if request.enabled else 'disabled'}"
        }

        logger.info("Successfully toggled manual override", status=status)
        return status

    except Exception as e:
        logger.error("Failed to toggle manual override", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to toggle manual override"
        )


@router.post("/enable", response_model=dict)
async def enable_manual_override(
    reason: str = "Manual enable request"
):
    """
    Enable manual trading override.

    Convenience endpoint to enable manual override mode, requiring
    manual approval for all trade executions.

    Args:
        reason: Reason for enabling override

    Returns:
        Updated override status
    """
    request = OverrideToggleRequest(enabled=True, reason=reason)
    return await toggle_manual_override(request)


@router.post("/disable", response_model=dict)
async def disable_manual_override(
    reason: str = "Manual disable request"
):
    """
    Disable manual trading override.

    Convenience endpoint to disable manual override mode, allowing
    automatic trade execution based on signals.

    Args:
        reason: Reason for disabling override

    Returns:
        Updated override status
    """
    request = OverrideToggleRequest(enabled=False, reason=reason)
    return await toggle_manual_override(request)


@router.get("/config", response_model=dict)
async def get_trading_config():
    """
    Get current trading configuration parameters.

    This endpoint returns the current trading configuration including
    signal thresholds, risk parameters, and override settings.

    Returns:
        Dictionary containing trading configuration
    """
    try:
        logger.info("Fetching trading configuration")

        config = {
            "signal_threshold": settings.trading.signal_threshold,
            "position_size_percent": settings.trading.position_size_percent,
            "stop_loss_percent": settings.trading.stop_loss_percent,
            "take_profit_percent": settings.trading.take_profit_percent,
            "max_daily_drawdown": settings.trading.max_daily_drawdown,
            "max_open_positions": settings.trading.max_open_positions,
            "manual_override": settings.trading.manual_override,
            "current_override_state": _override_state["enabled"]
        }

        logger.info("Successfully retrieved trading configuration")
        return config

    except Exception as e:
        logger.error("Failed to retrieve trading configuration", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trading configuration"
        )


# Import datetime for timestamp generation
