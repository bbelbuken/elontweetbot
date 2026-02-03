"""Risk management API endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.risk_manager import risk_manager
from workers.trade_executor import TradeExecutor
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk Management"])


class ManualOverrideRequest(BaseModel):
    """Request model for manual override toggle."""
    enabled: bool


class TradeApprovalRequest(BaseModel):
    """Request model for trade approval."""
    action: str  # 'approve' or 'reject'
    reason: str = None


@router.get("/status")
async def get_risk_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get comprehensive risk management status.

    Returns:
        Risk status information including drawdown, position limits, and manual override
    """
    try:
        status = risk_manager.get_risk_status(db)
        return status
    except Exception as e:
        logger.error(f"Error getting risk status", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get risk status")


@router.post("/manual-override/toggle")
async def toggle_manual_override() -> Dict[str, Any]:
    """
    Toggle manual override mode.

    Returns:
        New manual override status
    """
    try:
        new_status = risk_manager.toggle_manual_override()
        return {
            "manual_override": new_status,
            "message": f"Manual override {'enabled' if new_status else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error toggling manual override", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to toggle manual override")


@router.post("/manual-override")
async def set_manual_override(request: ManualOverrideRequest) -> Dict[str, Any]:
    """
    Set manual override mode.

    Args:
        request: Manual override request

    Returns:
        New manual override status
    """
    try:
        new_status = risk_manager.set_manual_override(request.enabled)
        return {
            "manual_override": new_status,
            "message": f"Manual override {'enabled' if new_status else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error setting manual override", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to set manual override")


@router.get("/pending-trades")
async def get_pending_trades() -> List[Dict[str, Any]]:
    """
    Get all pending trades awaiting approval.

    Returns:
        List of pending trades
    """
    try:
        pending_trades = risk_manager.get_pending_trades()
        return pending_trades
    except Exception as e:
        logger.error(f"Error getting pending trades", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get pending trades")


@router.post("/pending-trades/{trade_id}")
async def handle_trade_approval(
    trade_id: str,
    request: TradeApprovalRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve or reject a pending trade.

    Args:
        trade_id: ID of pending trade
        request: Trade approval request
        db: Database session

    Returns:
        Result of approval/rejection
    """
    try:
        if request.action == "approve":
            # Approve the trade
            approved_trade = risk_manager.approve_trade(trade_id)
            if not approved_trade:
                raise HTTPException(
                    status_code=404, detail="Pending trade not found")

            # Execute the approved trade
            executor = TradeExecutor()
            executed_trade = executor.execute_approved_trade(db, trade_id)

            if executed_trade:
                return {
                    "status": "approved_and_executed",
                    "trade_id": executed_trade.id,
                    "pending_trade_id": trade_id,
                    "message": "Trade approved and executed successfully"
                }
            else:
                return {
                    "status": "approved_but_failed",
                    "pending_trade_id": trade_id,
                    "message": "Trade approved but execution failed"
                }

        elif request.action == "reject":
            # Reject the trade
            rejected_trade = risk_manager.reject_trade(
                trade_id, request.reason)
            if not rejected_trade:
                raise HTTPException(
                    status_code=404, detail="Pending trade not found")

            return {
                "status": "rejected",
                "pending_trade_id": trade_id,
                "reason": request.reason,
                "message": "Trade rejected successfully"
            }
        else:
            raise HTTPException(
                status_code=400, detail="Invalid action. Use 'approve' or 'reject'")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling trade approval",
                     trade_id=trade_id, error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to handle trade approval")


@router.get("/drawdown")
async def get_drawdown_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current daily drawdown status.

    Returns:
        Drawdown status and limits
    """
    try:
        drawdown_status = risk_manager.check_daily_drawdown_limit(db)
        return drawdown_status
    except Exception as e:
        logger.error(f"Error getting drawdown status", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get drawdown status")


@router.get("/positions")
async def get_position_limits_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current position limits status.

    Returns:
        Position limits status
    """
    try:
        position_status = risk_manager.check_position_limits(db)
        return position_status
    except Exception as e:
        logger.error(f"Error getting position limits status", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to get position limits status")


@router.post("/cleanup")
async def cleanup_old_pending_trades(hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old pending trades.

    Args:
        hours: Age threshold in hours (default: 24)

    Returns:
        Cleanup result
    """
    try:
        cleaned_count = risk_manager.cleanup_old_pending_trades(hours)
        return {
            "cleaned_count": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old pending trades"
        }
    except Exception as e:
        logger.error(f"Error cleaning up pending trades", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to cleanup pending trades")
