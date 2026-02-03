"""
Trade API endpoints for retrieving trade history and execution data.

This module provides endpoints for:
- Trade history with filtering and pagination
- Open trades monitoring
- Trade statistics and PnL data
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.models.trade import Trade
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/", response_model=List[dict])
async def get_trade_history(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200,
                       description="Number of trades to return"),
    hours: int = Query(default=168, ge=1, le=8760,
                       description="Hours to look back (default 7 days)"),
    symbol: Optional[str] = Query(
        default=None, description="Filter by trading symbol"),
    status: Optional[str] = Query(
        default=None, description="Filter by trade status (OPEN, CLOSED, CANCELLED)"),
    side: Optional[str] = Query(
        default=None, description="Filter by trade side (LONG, SHORT)")
):
    """
    Get trade history with optional filtering.

    This endpoint retrieves historical trades with various filtering options
    for analysis and monitoring purposes.

    Args:
        db: Database session
        limit: Maximum number of trades to return (1-200)
        hours: Number of hours to look back (1-8760, default 7 days)
        symbol: Filter by specific trading symbol (e.g., 'BTCUSDT')
        status: Filter by trade status ('OPEN', 'CLOSED', 'CANCELLED')
        side: Filter by trade side ('LONG', 'SHORT')

    Returns:
        List of trade dictionaries with execution details and PnL

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching trade history",
                    limit=limit,
                    hours=hours,
                    symbol=symbol,
                    status=status,
                    side=side)

        # Start with recent trades or symbol-specific trades
        if symbol:
            trades = Trade.get_by_symbol(db, symbol=symbol, limit=limit)
        else:
            trades = Trade.get_recent(db, hours=hours, limit=limit)

        # Apply additional filters
        if status:
            trades = [trade for trade in trades if trade.status == status.upper()]

        if side:
            trades = [trade for trade in trades if trade.side == side.upper()]

        # Convert to dictionaries
        trade_data = [trade.to_dict() for trade in trades]

        logger.info("Successfully retrieved trade history",
                    count=len(trade_data))
        return trade_data

    except Exception as e:
        logger.error("Failed to retrieve trade history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trade history"
        )


@router.get("/open", response_model=List[dict])
async def get_open_trades(
    db: Session = Depends(get_db)
):
    """
    Get all currently open trades.

    This endpoint retrieves all trades that are currently open and active,
    useful for monitoring current positions and risk exposure.

    Args:
        db: Database session

    Returns:
        List of open trade dictionaries

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching open trades")

        trades = Trade.get_open_trades(db)
        trade_data = [trade.to_dict() for trade in trades]

        logger.info("Successfully retrieved open trades",
                    count=len(trade_data))
        return trade_data

    except Exception as e:
        logger.error("Failed to retrieve open trades", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve open trades"
        )


@router.get("/stats", response_model=dict)
async def get_trade_statistics(
    db: Session = Depends(get_db)
):
    """
    Get trading statistics and performance metrics.

    This endpoint provides summary statistics about trading performance
    including total PnL, win rate, and position counts.

    Args:
        db: Database session

    Returns:
        Dictionary containing trading statistics

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Calculating trade statistics")

        # Get basic counts
        open_count = Trade.count_open_positions(db)
        total_pnl = Trade.get_total_pnl(db)
        daily_pnl = Trade.get_daily_pnl(db)

        # Get all closed trades for additional stats
        closed_trades = db.query(Trade).filter(Trade.status == 'CLOSED').all()

        # Calculate win/loss statistics
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]

        total_trades = len(closed_trades)
        win_rate = (len(winning_trades) / total_trades *
                    100) if total_trades > 0 else 0

        # Calculate average win/loss
        avg_win = sum(float(t.pnl) for t in winning_trades) / \
            len(winning_trades) if winning_trades else 0
        avg_loss = sum(float(t.pnl) for t in losing_trades) / \
            len(losing_trades) if losing_trades else 0

        stats = {
            "open_positions": open_count,
            "total_realized_pnl": float(total_pnl),
            "daily_pnl": float(daily_pnl),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_percent": round(win_rate, 2),
            "average_win": round(avg_win, 4),
            "average_loss": round(avg_loss, 4),
            "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
        }

        logger.info("Successfully calculated trade statistics", stats=stats)
        return stats

    except Exception as e:
        logger.error("Failed to calculate trade statistics",
                     error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate trade statistics: {str(e)}"
        )


@router.get("/{trade_id}", response_model=dict)
async def get_trade_by_id(
    trade_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific trade by its ID.

    Args:
        trade_id: Trade ID
        db: Database session

    Returns:
        Trade dictionary with execution details

    Raises:
        HTTPException: If trade not found or database query fails
    """
    try:
        logger.info("Fetching trade by ID", trade_id=trade_id)

        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=404,
                detail=f"Trade with ID {trade_id} not found"
            )

        trade_data = trade.to_dict()
        logger.info("Successfully retrieved trade", trade_id=trade_id)
        return trade_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve trade",
                     trade_id=trade_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trade"
        )
