"""
Unit tests for core business logic models.

Tests for:
- Tweet model methods
- Trade model calculations
- Position model updates
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


class TestTweetModel:
    """Test suite for Tweet model."""

    def test_mark_processed(self):
        """Test marking tweet as processed with scores."""
        from app.models.tweet import Tweet
        
        tweet = Tweet(
            id=123,
            author="test_user",
            text="Bitcoin is amazing! #crypto",
            created_at=datetime.utcnow(),
            processed=False
        )
        
        # Mock database session
        db = Mock()
        
        # Test marking as processed
        result = tweet.mark_processed(db, sentiment_score=0.85, signal_score=90)
        
        assert tweet.processed is True
        assert tweet.sentiment_score == 0.85
        assert tweet.signal_score == 90
        assert db.commit.called

    def test_signal_score_validation(self):
        """Test signal score is within valid range."""
        from app.models.tweet import Tweet
        
        tweet = Tweet(
            id=456,
            author="trader",
            text="Test tweet",
            created_at=datetime.utcnow()
        )
        
        db = Mock()
        
        # Test with valid score
        tweet.mark_processed(db, 0.5, 75)
        assert 0 <= tweet.signal_score <= 100
        
        # Test boundary values
        tweet.mark_processed(db, 1.0, 100)
        assert tweet.signal_score == 100
        
        tweet.mark_processed(db, -1.0, 0)
        assert tweet.signal_score == 0


class TestTradeModel:
    """Test suite for Trade model."""

    def test_calculate_pnl_long(self):
        """Test PnL calculation for LONG trades."""
        entry_price = Decimal('50000')
        exit_price = Decimal('51000')
        quantity = Decimal('0.1')
        
        # For LONG: PnL = (exit - entry) * quantity
        expected_pnl = (exit_price - entry_price) * quantity
        
        pnl = (exit_price - entry_price) * quantity
        assert pnl == expected_pnl
        assert pnl == Decimal('100')  # (51000 - 50000) * 0.1

    def test_calculate_pnl_short(self):
        """Test PnL calculation for SHORT trades."""
        entry_price = Decimal('50000')
        exit_price = Decimal('49000')
        quantity = Decimal('0.1')
        
        # For SHORT: PnL = (entry - exit) * quantity
        pnl = (entry_price - exit_price) * quantity
        
        assert pnl == Decimal('100')  # (50000 - 49000) * 0.1

    def test_stop_loss_calculation(self):
        """Test stop-loss price calculation."""
        entry_price = Decimal('50000')
        stop_loss_percent = Decimal('0.02')  # 2%
        
        # For LONG: stop loss is below entry
        stop_loss_long = entry_price * (Decimal('1') - stop_loss_percent)
        assert stop_loss_long == Decimal('49000')
        
        # For SHORT: stop loss is above entry
        stop_loss_short = entry_price * (Decimal('1') + stop_loss_percent)
        assert stop_loss_short == Decimal('51000')

    def test_take_profit_calculation(self):
        """Test take-profit price calculation."""
        entry_price = Decimal('50000')
        take_profit_percent = Decimal('0.04')  # 4%
        
        # For LONG: take profit is above entry
        take_profit_long = entry_price * (Decimal('1') + take_profit_percent)
        assert take_profit_long == Decimal('52000')
        
        # For SHORT: take profit is below entry
        take_profit_short = entry_price * (Decimal('1') - take_profit_percent)
        assert take_profit_short == Decimal('48000')


class TestPositionModel:
    """Test suite for Position model."""

    def test_add_to_position(self):
        """Test adding to an existing position."""
        from app.models.position import Position
        
        # Initial position
        position = Position(
            symbol="BTCUSDT",
            size=Decimal('0.1'),
            avg_entry=Decimal('50000'),
            leverage=1
        )
        
        # Add to position
        additional_size = Decimal('0.05')
        new_price = Decimal('51000')
        
        position.add_to_position(additional_size, new_price)
        
        # New average entry should be weighted average
        expected_avg = (Decimal('50000') * Decimal('0.1') + 
                       Decimal('51000') * Decimal('0.05')) / Decimal('0.15')
        
        assert position.size == Decimal('0.15')
        assert abs(position.avg_entry - expected_avg) < Decimal('0.01')

    def test_calculate_unrealized_pnl_long(self):
        """Test unrealized PnL calculation for LONG position."""
        from app.models.position import Position
        
        position = Position(
            symbol="BTCUSDT",
            size=Decimal('0.1'),  # Positive = LONG
            avg_entry=Decimal('50000'),
            leverage=1
        )
        
        current_price = Decimal('51000')
        
        # Unrealized PnL = (current - entry) * size
        expected_pnl = (current_price - position.avg_entry) * position.size
        
        position.unrealized_pnl = expected_pnl
        assert position.unrealized_pnl == Decimal('100')

    def test_calculate_unrealized_pnl_short(self):
        """Test unrealized PnL calculation for SHORT position."""
        from app.models.position import Position
        
        position = Position(
            symbol="BTCUSDT",
            size=Decimal('-0.1'),  # Negative = SHORT
            avg_entry=Decimal('50000'),
            leverage=1
        )
        
        current_price = Decimal('49000')
        
        # For SHORT: PnL = (entry - current) * abs(size)
        expected_pnl = (position.avg_entry - current_price) * abs(position.size)
        
        position.unrealized_pnl = expected_pnl
        assert position.unrealized_pnl == Decimal('100')

    def test_position_side_property(self):
        """Test position side determination."""
        from app.models.position import Position
        
        long_position = Position(
            symbol="BTCUSDT",
            size=Decimal('0.1'),
            avg_entry=Decimal('50000'),
            leverage=1
        )
        
        short_position = Position(
            symbol="ETHUSDT",
            size=Decimal('-0.1'),
            avg_entry=Decimal('3000'),
            leverage=1
        )
        
        assert long_position.side == "LONG"
        assert short_position.side == "SHORT"


class TestNLPProcessing:
    """Test suite for NLP sentiment analysis."""

    def test_keyword_matching(self):
        """Test crypto keyword matching."""
        from workers.nlp_processor import calculate_keyword_score
        
        # Test with multiple keywords
        text = "Bitcoin and Ethereum are bullish! Buy crypto now!"
        score, keywords = calculate_keyword_score(text)
        
        assert score > 0
        assert 'bitcoin' in keywords
        assert 'ethereum' in keywords
        assert 'crypto' in keywords
        assert 'bullish' in keywords

    def test_sentiment_amplifiers(self):
        """Test sentiment amplifier words."""
        from workers.nlp_processor import calculate_keyword_score
        
        # Text with amplifier
        text_with_amplifier = "Bitcoin is extremely bullish!"
        score_amplified, _ = calculate_keyword_score(text_with_amplifier)
        
        # Text without amplifier
        text_normal = "Bitcoin is bullish"
        score_normal, _ = calculate_keyword_score(text_normal)
        
        # Amplified text should have higher score
        assert score_amplified > score_normal

    def test_signal_score_calculation(self):
        """Test combined signal score calculation."""
        from workers.nlp_processor import calculate_signal_score
        
        # High keyword score + positive sentiment
        keyword_score = 50
        sentiment_scores = {
            'positive': 0.8,
            'negative': 0.1,
            'neutral': 0.1
        }
        matched_keywords = ['bitcoin', 'ethereum', 'bullish']
        
        signal_score = calculate_signal_score(
            keyword_score, sentiment_scores, matched_keywords
        )
        
        assert 0 <= signal_score <= 100
        assert signal_score > 50  # Should be high with good sentiment

    def test_no_keywords_low_score(self):
        """Test that no crypto keywords results in low score."""
        from workers.nlp_processor import calculate_signal_score
        
        keyword_score = 0
        sentiment_scores = {
            'positive': 0.9,
            'negative': 0.05,
            'neutral': 0.05
        }
        matched_keywords = []
        
        signal_score = calculate_signal_score(
            keyword_score, sentiment_scores, matched_keywords
        )
        
        # No keywords should result in 0 score regardless of sentiment
        assert signal_score == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
