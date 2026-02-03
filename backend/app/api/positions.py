"""
Position API endpoints for retrieving current position data.

This module provides endpoints for:
- Current open positions
- Position-specific data and unrealized PnL
- Position statistics and risk metrics
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.models.position import Position
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=List[dict])
async def get_current_positions(
    db: Session = Depends(get_db),
    side: Optional[str] = Query(
        default=None, description="Filter by position side (LONG, SHORT)")
):
    """
    Get all current open positions.

    This endpoint retrieves all active positions with their current status,
    unrealized PnL, and position details.

    Args:
        db: Database session
        side: Optional filter by position side ('LONG' or 'SHORT')

    Returns:
        List of position dictionaries with current status and PnL

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching current positions", side=side)

        # Get positions based on side filter
        if side and side.upper() == "LONG":
            positions = Position.get_long_positions(db)
        elif side and side.upper() == "SHORT":
            positions = Position.get_short_positions(db)
        else:
            positions = Position.get_all_positions(db)

        # Convert to dictionaries
        position_data = [position.to_dict() for position in positions]

        logger.info("Successfully retrieved positions",
                    count=len(position_data))
        return position_data

    except Exception as e:
        logger.error("Failed to retrieve positions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve positions"
        )


@router.get("/summary", response_model=dict)
async def get_positions_summary(
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for all current positions.

    This endpoint provides aggregated data about current positions
    including total unrealized PnL, position counts, and risk metrics.

    Args:
        db: Database session

    Returns:
        Dictionary containing position summary statistics

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Calculating positions summary")

        # Get all positions
        all_positions = Position.get_all_positions(db)
        long_positions = Position.get_long_positions(db)
        short_positions = Position.get_short_positions(db)

        # Calculate total unrealized PnL
        total_unrealized_pnl = Position.get_total_unrealized_pnl(db)

        # Calculate position values
        total_position_value = sum(
            float(pos.abs_size) * float(pos.avg_entry)
            for pos in all_positions
        )

        # Calculate average entry prices by side
        long_avg_entry = (
            sum(float(pos.avg_entry)
                for pos in long_positions) / len(long_positions)
            if long_positions else 0
        )
        short_avg_entry = (
            sum(float(pos.avg_entry)
                for pos in short_positions) / len(short_positions)
            if short_positions else 0
        )

        # Get symbols for diversity metrics
        symbols = list(set(pos.symbol for pos in all_positions))

        summary = {
            "total_positions": len(all_positions),
            "long_positions": len(long_positions),
            "short_positions": len(short_positions),
            "total_unrealized_pnl": float(total_unrealized_pnl),
            "total_position_value": round(total_position_value, 2),
            "symbols_traded": len(symbols),
            "symbols": symbols,
            "average_long_entry": round(long_avg_entry, 4),
            "average_short_entry": round(short_avg_entry, 4),
            "net_exposure": len(long_positions) - len(short_positions)
        }

        logger.info("Successfully calculated positions summary",
                    summary=summary)
        return summary

    except Exception as e:
        logger.error("Failed to calculate positions summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate positions summary"
        )


@router.get("/{symbol}", response_model=dict)
async def get_position_by_symbol(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get position data for a specific trading symbol.

    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        db: Database session

    Returns:
        Position dictionary with current status and PnL

    Raises:
        HTTPException: If position not found or database query fails
    """
    try:
        logger.info("Fetching position by symbol", symbol=symbol)

        position = Position.get_by_symbol(db, symbol=symbol.upper())
        if not position:
            raise HTTPException(
                status_code=404,
                detail=f"No position found for symbol {symbol}"
            )

        position_data = position.to_dict()
        logger.info("Successfully retrieved position", symbol=symbol)
        return position_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve position",
                     symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve position"
        )


@router.put("/{symbol}/pnl", response_model=dict)
async def update_position_pnl(
    symbol: str,
    current_price: float,
    db: Session = Depends(get_db)
):
    """
    Update unrealized PnL for a position based on current market price.

    This endpoint allows manual updating of position PnL for testing
    or when market data updates are needed.

    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        current_price: Current market price for PnL calculation
        db: Database session

    Returns:
        Updated position dictionary with new unrealized PnL

    Raises:
        HTTPException: If position not found or update fails
    """
    try:
        logger.info("Updating position PnL", symbol=symbol,
                    current_price=current_price)

        if current_price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Current price must be greater than 0"
            )

        position = Position.update_pnl_for_symbol(
            db,
            symbol=symbol.upper(),
            current_price=Decimal(str(current_price))
        )

        if not position:
            raise HTTPException(
                status_code=404,
                detail=f"No position found for symbol {symbol}"
            )

        position_data = position.to_dict()
        logger.info("Successfully updated position PnL",
                    symbol=symbol,
                    unrealized_pnl=position_data.get("unrealized_pnl"))
        return position_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update position PnL",
                     symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to update position PnL"
        )
