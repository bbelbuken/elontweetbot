"""Risk management service for trading controls and limits."""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.models.position import Position
from app.clients.binance_client import BinanceClient
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RiskManager:
    """Risk management service with trading controls and limits."""

    def __init__(self):
        """Initialize risk manager."""
        self.binance_client = BinanceClient()
        self._manual_override = settings.trading.manual_override
        self._pending_trades: List[Dict] = []  # Store trades awaiting approval

    @property
    def manual_override(self) -> bool:
        """Get current manual override status."""
        return self._manual_override

    def toggle_manual_override(self) -> bool:
        """
        Toggle manual override mode.

        Returns:
            New manual override status
        """
        self._manual_override = not self._manual_override
        logger.info(f"Manual override toggled", status=self._manual_override)
        return self._manual_override

    def set_manual_override(self, enabled: bool) -> bool:
        """
        Set manual override mode.

        Args:
            enabled: Whether to enable manual override

        Returns:
            New manual override status
        """
        self._manual_override = enabled
        logger.info(f"Manual override set", status=self._manual_override)
        return self._manual_override

    def check_daily_drawdown_limit(self, db: Session) -> Dict[str, any]:
        """
        Check if daily drawdown limit has been reached.

        Args:
            db: Database session

        Returns:
            Dict with status and details
        """
        try:
            today = datetime.utcnow().date()
            daily_pnl = Trade.get_daily_pnl(
                db, datetime.combine(today, datetime.min.time()))

            # Get account balance
            account_balance = self.binance_client.get_balance('USDT')
            if account_balance <= 0:
                return {
                    "allowed": False,
                    "reason": "zero_balance",
                    "daily_pnl": float(daily_pnl),
                    "account_balance": float(account_balance),
                    "drawdown_percent": 0.0,
                    "max_drawdown": float(settings.trading.max_daily_drawdown)
                }

            # Calculate drawdown percentage
            drawdown_percent = abs(
                daily_pnl) / account_balance if daily_pnl < 0 else Decimal('0')
            max_drawdown = Decimal(str(settings.trading.max_daily_drawdown))

            allowed = drawdown_percent < max_drawdown

            result = {
                "allowed": allowed,
                "reason": "drawdown_limit" if not allowed else None,
                "daily_pnl": float(daily_pnl),
                "account_balance": float(account_balance),
                "drawdown_percent": float(drawdown_percent),
                "max_drawdown": float(max_drawdown)
            }

            if not allowed:
                logger.warning("Daily drawdown limit reached", **result)

            return result

        except Exception as e:
            logger.error(f"Error checking daily drawdown", error=str(e))
            return {
                "allowed": False,
                "reason": "error",
                "error": str(e)
            }

    def check_position_limits(self, db: Session) -> Dict[str, any]:
        """
        Check if maximum position limit has been reached.

        Args:
            db: Database session

        Returns:
            Dict with status and details
        """
        try:
            open_positions = Trade.count_open_positions(db)
            max_positions = settings.trading.max_open_positions

            allowed = open_positions < max_positions

            result = {
                "allowed": allowed,
                "reason": "position_limit" if not allowed else None,
                "open_positions": open_positions,
                "max_positions": max_positions
            }

            if not allowed:
                logger.warning("Maximum position limit reached", **result)

            return result

        except Exception as e:
            logger.error(f"Error checking position limits", error=str(e))
            return {
                "allowed": False,
                "reason": "error",
                "error": str(e)
            }

    def validate_trade_request(self, db: Session, symbol: str, side: str, quantity: Decimal) -> Dict[str, any]:
        """
        Validate a trade request against all risk management rules.

        Args:
            db: Database session
            symbol: Trading pair symbol
            side: Trade side ('LONG' or 'SHORT')
            quantity: Trade quantity

        Returns:
            Dict with validation result and details
        """
        validation_result = {
            "allowed": True,
            "reasons": [],
            "checks": {}
        }

        # Check daily drawdown limit
        drawdown_check = self.check_daily_drawdown_limit(db)
        validation_result["checks"]["drawdown"] = drawdown_check
        if not drawdown_check["allowed"]:
            validation_result["allowed"] = False
            validation_result["reasons"].append(drawdown_check["reason"])

        # Check position limits
        position_check = self.check_position_limits(db)
        validation_result["checks"]["positions"] = position_check
        if not position_check["allowed"]:
            validation_result["allowed"] = False
            validation_result["reasons"].append(position_check["reason"])

        # Check manual override mode
        if self.manual_override:
            validation_result["requires_approval"] = True
            validation_result["reasons"].append("manual_override_enabled")
        else:
            validation_result["requires_approval"] = False

        return validation_result

    def add_pending_trade(self, tweet_id: int, symbol: str, side: str, quantity: Decimal, signal_score: int) -> str:
        """
        Add a trade to pending approval queue.

        Args:
            tweet_id: ID of tweet that generated the signal
            symbol: Trading pair symbol
            side: Trade side ('LONG' or 'SHORT')
            quantity: Trade quantity
            signal_score: Signal score that triggered the trade

        Returns:
            Pending trade ID
        """
        pending_trade = {
            "id": f"pending_{len(self._pending_trades) + 1}_{datetime.utcnow().timestamp()}",
            "tweet_id": tweet_id,
            "symbol": symbol,
            "side": side,
            "quantity": float(quantity),
            "signal_score": signal_score,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        self._pending_trades.append(pending_trade)
        logger.info(f"Trade added to pending approval",
                    trade_id=pending_trade["id"])

        return pending_trade["id"]

    def get_pending_trades(self) -> List[Dict]:
        """
        Get all pending trades awaiting approval.

        Returns:
            List of pending trades
        """
        return [trade for trade in self._pending_trades if trade["status"] == "pending"]

    def approve_trade(self, pending_trade_id: str) -> Optional[Dict]:
        """
        Approve a pending trade.

        Args:
            pending_trade_id: ID of pending trade to approve

        Returns:
            Approved trade details or None if not found
        """
        for trade in self._pending_trades:
            if trade["id"] == pending_trade_id and trade["status"] == "pending":
                trade["status"] = "approved"
                trade["approved_at"] = datetime.utcnow().isoformat()
                logger.info(f"Trade approved", trade_id=pending_trade_id)
                return trade

        logger.warning(f"Pending trade not found", trade_id=pending_trade_id)
        return None

    def reject_trade(self, pending_trade_id: str, reason: str = None) -> Optional[Dict]:
        """
        Reject a pending trade.

        Args:
            pending_trade_id: ID of pending trade to reject
            reason: Reason for rejection

        Returns:
            Rejected trade details or None if not found
        """
        for trade in self._pending_trades:
            if trade["id"] == pending_trade_id and trade["status"] == "pending":
                trade["status"] = "rejected"
                trade["rejected_at"] = datetime.utcnow().isoformat()
                trade["rejection_reason"] = reason
                logger.info(f"Trade rejected",
                            trade_id=pending_trade_id, reason=reason)
                return trade

        logger.warning(f"Pending trade not found", trade_id=pending_trade_id)
        return None

    def cleanup_old_pending_trades(self, hours: int = 24) -> int:
        """
        Clean up old pending trades.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of trades cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        initial_count = len(self._pending_trades)

        self._pending_trades = [
            trade for trade in self._pending_trades
            if datetime.fromisoformat(trade["created_at"]) > cutoff_time
        ]

        cleaned_count = initial_count - len(self._pending_trades)
        if cleaned_count > 0:
            logger.info(f"Cleaned up old pending trades", count=cleaned_count)

        return cleaned_count

    def get_risk_status(self, db: Session) -> Dict[str, any]:
        """
        Get comprehensive risk management status.

        Args:
            db: Database session

        Returns:
            Dict with risk status information
        """
        drawdown_check = self.check_daily_drawdown_limit(db)
        position_check = self.check_position_limits(db)

        return {
            "manual_override": self.manual_override,
            "trading_allowed": drawdown_check["allowed"] and position_check["allowed"],
            "drawdown_status": drawdown_check,
            "position_status": position_check,
            "pending_trades_count": len(self.get_pending_trades()),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global risk manager instance
risk_manager = RiskManager()
