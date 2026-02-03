"""Tests for risk management functionality."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.risk_manager import RiskManager
from app.models.trade import Trade
from app.models.position import Position


class TestRiskManager:
    """Test cases for RiskManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.risk_manager = RiskManager()

    def test_manual_override_toggle(self):
        """Test manual override toggle functionality."""
        # Test initial state
        initial_state = self.risk_manager.manual_override

        # Toggle override
        new_state = self.risk_manager.toggle_manual_override()
        assert new_state != initial_state
        assert self.risk_manager.manual_override == new_state

        # Toggle back
        final_state = self.risk_manager.toggle_manual_override()
        assert final_state == initial_state
        assert self.risk_manager.manual_override == final_state

    def test_set_manual_override(self):
        """Test manual override set functionality."""
        # Set to True
        result = self.risk_manager.set_manual_override(True)
        assert result is True
        assert self.risk_manager.manual_override is True

        # Set to False
        result = self.risk_manager.set_manual_override(False)
        assert result is False
        assert self.risk_manager.manual_override is False

    def test_add_pending_trade(self):
        """Test adding trades to pending approval queue."""
        # Add a pending trade
        trade_id = self.risk_manager.add_pending_trade(
            tweet_id=123,
            symbol="BTCUSDT",
            side="LONG",
            quantity=Decimal("0.001"),
            signal_score=85
        )

        assert trade_id is not None
        assert trade_id.startswith("pending_")

        # Check pending trades
        pending_trades = self.risk_manager.get_pending_trades()
        assert len(pending_trades) == 1
        assert pending_trades[0]["tweet_id"] == 123
        assert pending_trades[0]["symbol"] == "BTCUSDT"
        assert pending_trades[0]["side"] == "LONG"
        assert pending_trades[0]["signal_score"] == 85

    def test_approve_trade(self):
        """Test trade approval functionality."""
        # Add a pending trade
        trade_id = self.risk_manager.add_pending_trade(
            tweet_id=123,
            symbol="BTCUSDT",
            side="LONG",
            quantity=Decimal("0.001"),
            signal_score=85
        )

        # Approve the trade
        approved_trade = self.risk_manager.approve_trade(trade_id)
        assert approved_trade is not None
        assert approved_trade["status"] == "approved"
        assert "approved_at" in approved_trade

        # Check pending trades (should be empty now)
        pending_trades = self.risk_manager.get_pending_trades()
        assert len(pending_trades) == 0

    def test_reject_trade(self):
        """Test trade rejection functionality."""
        # Add a pending trade
        trade_id = self.risk_manager.add_pending_trade(
            tweet_id=123,
            symbol="BTCUSDT",
            side="LONG",
            quantity=Decimal("0.001"),
            signal_score=85
        )

        # Reject the trade
        rejected_trade = self.risk_manager.reject_trade(
            trade_id, "Test rejection")
        assert rejected_trade is not None
        assert rejected_trade["status"] == "rejected"
        assert rejected_trade["rejection_reason"] == "Test rejection"
        assert "rejected_at" in rejected_trade

        # Check pending trades (should be empty now)
        pending_trades = self.risk_manager.get_pending_trades()
        assert len(pending_trades) == 0

    def test_cleanup_old_pending_trades(self):
        """Test cleanup of old pending trades."""
        # Add some trades
        trade_id_1 = self.risk_manager.add_pending_trade(
            tweet_id=123, symbol="BTCUSDT", side="LONG",
            quantity=Decimal("0.001"), signal_score=85
        )
        trade_id_2 = self.risk_manager.add_pending_trade(
            tweet_id=124, symbol="ETHUSDT", side="SHORT",
            quantity=Decimal("0.01"), signal_score=90
        )

        # Manually set one trade to be old
        for trade in self.risk_manager._pending_trades:
            if trade["id"] == trade_id_1:
                old_time = datetime.utcnow() - timedelta(hours=25)
                trade["created_at"] = old_time.isoformat()

        # Cleanup old trades (older than 24 hours)
        cleaned_count = self.risk_manager.cleanup_old_pending_trades(hours=24)
        assert cleaned_count == 1

        # Check remaining trades
        pending_trades = self.risk_manager.get_pending_trades()
        assert len(pending_trades) == 1
        assert pending_trades[0]["id"] == trade_id_2

    @patch('app.services.risk_manager.BinanceClient')
    def test_check_daily_drawdown_limit(self, mock_binance_client):
        """Test daily drawdown limit checking."""
        # Mock database session
        mock_db = Mock()

        # Mock Binance client instance
        mock_client_instance = Mock()
        mock_client_instance.get_balance.return_value = Decimal(
            "1000")  # $1000 balance
        mock_binance_client.return_value = mock_client_instance

        # Create a new risk manager with mocked client
        risk_manager = RiskManager()
        risk_manager.binance_client = mock_client_instance

        # Mock Trade.get_daily_pnl to return -30 (3% loss)
        with patch.object(Trade, 'get_daily_pnl', return_value=Decimal("-30")):
            result = risk_manager.check_daily_drawdown_limit(mock_db)

            assert result["allowed"] is True  # 3% < 5% limit
            assert result["daily_pnl"] == -30.0
            assert result["account_balance"] == 1000.0
            assert result["drawdown_percent"] == 0.03

        # Test with higher loss (6% loss, should exceed 5% limit)
        with patch.object(Trade, 'get_daily_pnl', return_value=Decimal("-60")):
            result = risk_manager.check_daily_drawdown_limit(mock_db)

            assert result["allowed"] is False  # 6% > 5% limit
            assert result["reason"] == "drawdown_limit"
            assert result["drawdown_percent"] == 0.06

    def test_check_position_limits(self):
        """Test position limits checking."""
        # Mock database session
        mock_db = Mock()

        # Mock Trade.count_open_positions to return 3 positions
        with patch.object(Trade, 'count_open_positions', return_value=3):
            result = self.risk_manager.check_position_limits(mock_db)

            assert result["allowed"] is True  # 3 < 5 limit
            assert result["open_positions"] == 3
            assert result["max_positions"] == 5

        # Test with max positions reached
        with patch.object(Trade, 'count_open_positions', return_value=5):
            result = self.risk_manager.check_position_limits(mock_db)

            assert result["allowed"] is False  # 5 >= 5 limit
            assert result["reason"] == "position_limit"

    @patch('app.services.risk_manager.BinanceClient')
    def test_validate_trade_request(self, mock_binance_client):
        """Test comprehensive trade request validation."""
        # Mock database session
        mock_db = Mock()

        # Mock Binance client instance
        mock_client_instance = Mock()
        mock_client_instance.get_balance.return_value = Decimal("1000")
        mock_binance_client.return_value = mock_client_instance

        # Create a new risk manager with mocked client
        risk_manager = RiskManager()
        risk_manager.binance_client = mock_client_instance

        # Mock successful checks
        with patch.object(Trade, 'get_daily_pnl', return_value=Decimal("-10")), \
                patch.object(Trade, 'count_open_positions', return_value=2):

            # Test with manual override disabled
            risk_manager.set_manual_override(False)
            result = risk_manager.validate_trade_request(
                mock_db, "BTCUSDT", "LONG", Decimal("0.001")
            )

            assert result["allowed"] is True
            assert result["requires_approval"] is False
            assert len(result["reasons"]) == 0

            # Test with manual override enabled
            risk_manager.set_manual_override(True)
            result = risk_manager.validate_trade_request(
                mock_db, "BTCUSDT", "LONG", Decimal("0.001")
            )

            assert result["allowed"] is True
            assert result["requires_approval"] is True
            assert "manual_override_enabled" in result["reasons"]
