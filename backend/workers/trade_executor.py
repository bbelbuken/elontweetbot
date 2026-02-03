"""Trade execution worker for processing trading signals and managing positions."""

from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from workers.celery_app import celery_app
from app.database import get_db
from app.models.trade import Trade
from app.models.position import Position
from app.models.tweet import Tweet
from app.clients.binance_client import BinanceClient
from app.services.risk_manager import risk_manager
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TradeExecutor:
    """Trade execution service with risk management."""

    def __init__(self):
        """Initialize trade executor."""
        self.binance_client = BinanceClient()
        self.config = settings.trading

    def calculate_position_size(self, account_balance: Decimal, symbol: str, current_price: Decimal) -> Decimal:
        """
        Calculate position size based on account balance and risk percentage.

        Args:
            account_balance: Available account balance in USDT
            symbol: Trading pair symbol
            current_price: Current market price

        Returns:
            Position size in base asset
        """
        # Calculate position value (1% of account balance)
        position_value = account_balance * \
            Decimal(str(self.config.position_size_percent))

        # Calculate quantity in base asset
        quantity = position_value / current_price

        # Round down to avoid insufficient balance errors
        # Get symbol info to determine precision
        symbol_info = self.binance_client.get_symbol_info(symbol)
        if symbol_info:
            # Find LOT_SIZE filter for quantity precision
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    step_size = Decimal(filter_info['stepSize'])
                    # Round down to step size
                    quantity = (quantity / step_size).quantize(Decimal('1'),
                                                               rounding=ROUND_DOWN) * step_size
                    break

        logger.info(f"Calculated position size",
                    symbol=symbol, account_balance=str(account_balance),
                    position_value=str(position_value), quantity=str(quantity))

        return quantity

    def calculate_stop_loss_price(self, entry_price: Decimal, side: str) -> Decimal:
        """
        Calculate stop-loss price based on entry price and risk percentage.

        Args:
            entry_price: Entry price
            side: Trade side ('LONG' or 'SHORT')

        Returns:
            Stop-loss price
        """
        stop_loss_percent = Decimal(str(self.config.stop_loss_percent))

        if side == 'LONG':
            # For long positions, stop-loss is below entry price
            stop_loss = entry_price * (Decimal('1') - stop_loss_percent)
        else:  # SHORT
            # For short positions, stop-loss is above entry price
            stop_loss = entry_price * (Decimal('1') + stop_loss_percent)

        return stop_loss

    def calculate_take_profit_price(self, entry_price: Decimal, side: str) -> Decimal:
        """
        Calculate take-profit price based on entry price and profit percentage.

        Args:
            entry_price: Entry price
            side: Trade side ('LONG' or 'SHORT')

        Returns:
            Take-profit price
        """
        take_profit_percent = Decimal(str(self.config.take_profit_percent))

        if side == 'LONG':
            # For long positions, take-profit is above entry price
            take_profit = entry_price * (Decimal('1') + take_profit_percent)
        else:  # SHORT
            # For short positions, take-profit is below entry price
            take_profit = entry_price * (Decimal('1') - take_profit_percent)

        return take_profit

    def execute_trade_signal(self, db: Session, tweet_id: int, symbol: str, side: str) -> Optional[Trade]:
        """
        Execute a trade based on signal with risk management validation.

        Args:
            db: Database session
            tweet_id: ID of tweet that generated the signal
            symbol: Trading pair symbol
            side: Trade side ('LONG' or 'SHORT')

        Returns:
            Created trade or None if failed/rejected
        """
        try:
            # Get current market price
            current_price = self.binance_client.get_ticker_price(symbol)
            if not current_price:
                logger.error(f"Failed to get current price for {symbol}")
                return None

            # Get account balance
            account_balance = self.binance_client.get_balance('USDT')
            if account_balance <= 0:
                logger.error("Insufficient account balance")
                return None

            # Calculate position size
            quantity = self.calculate_position_size(
                account_balance, symbol, current_price)
            if quantity <= 0:
                logger.error("Invalid position size calculated")
                return None

            # Validate trade request with risk management
            validation = risk_manager.validate_trade_request(
                db, symbol, side, quantity)

            if not validation["allowed"]:
                logger.warning("Trade rejected by risk management",
                               reasons=validation["reasons"],
                               checks=validation["checks"])
                return None

            # If manual override is enabled, add to pending trades
            if validation.get("requires_approval", False):
                # Get tweet for signal score
                tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
                signal_score = tweet.signal_score if tweet else 0

                pending_id = risk_manager.add_pending_trade(
                    tweet_id, symbol, side, quantity, signal_score)
                logger.info(f"Trade added to pending approval queue",
                            pending_id=pending_id)
                return None  # Trade not executed, awaiting approval

            # Execute the trade
            return self._execute_trade_internal(db, tweet_id, symbol, side, quantity, current_price)

        except Exception as e:
            logger.error(f"Error executing trade", error=str(e))
            db.rollback()
            return None

    def execute_approved_trade(self, db: Session, pending_trade_id: str) -> Optional[Trade]:
        """
        Execute a previously approved trade.

        Args:
            db: Database session
            pending_trade_id: ID of approved pending trade

        Returns:
            Created trade or None if failed
        """
        try:
            # Get approved trade details
            approved_trade = risk_manager.approve_trade(pending_trade_id)
            if not approved_trade:
                logger.error(f"Approved trade not found",
                             trade_id=pending_trade_id)
                return None

            # Get current market price (price may have changed since approval)
            current_price = self.binance_client.get_ticker_price(
                approved_trade["symbol"])
            if not current_price:
                logger.error(
                    f"Failed to get current price for {approved_trade['symbol']}")
                return None

            # Execute the trade
            quantity = Decimal(str(approved_trade["quantity"]))
            return self._execute_trade_internal(
                db, approved_trade["tweet_id"], approved_trade["symbol"],
                approved_trade["side"], quantity, current_price)

        except Exception as e:
            logger.error(f"Error executing approved trade", error=str(e))
            return None

    def _execute_trade_internal(self, db: Session, tweet_id: int, symbol: str, side: str,
                                quantity: Decimal, current_price: Decimal) -> Optional[Trade]:
        """
        Internal method to execute a trade after validation.

        Args:
            db: Database session
            tweet_id: ID of tweet that generated the signal
            symbol: Trading pair symbol
            side: Trade side ('LONG' or 'SHORT')
            quantity: Trade quantity
            current_price: Current market price

        Returns:
            Created trade or None if failed
        """
        try:
            # Calculate stop-loss and take-profit prices
            stop_loss_price = self.calculate_stop_loss_price(
                current_price, side)
            take_profit_price = self.calculate_take_profit_price(
                current_price, side)

            # Determine Binance order side
            binance_side = 'BUY' if side == 'LONG' else 'SELL'

            # Place market order
            order_response = self.binance_client.place_market_order(
                symbol, binance_side, quantity)
            if not order_response:
                logger.error("Failed to place market order")
                return None

            # Create trade record
            trade = Trade(
                tweet_id=tweet_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=current_price,  # Will be updated with actual fill price
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                status='OPEN'
            )

            db.add(trade)
            db.commit()
            db.refresh(trade)

            # Update position
            self.update_position(db, symbol, side, quantity, current_price)

            logger.info(f"Trade executed successfully",
                        trade_id=trade.id, symbol=symbol, side=side,
                        quantity=str(quantity), entry_price=str(current_price))

            return trade

        except Exception as e:
            logger.error(f"Error in internal trade execution", error=str(e))
            db.rollback()
            return None

    def update_position(self, db: Session, symbol: str, side: str, quantity: Decimal, price: Decimal) -> None:
        """
        Update position after trade execution.

        Args:
            db: Database session
            symbol: Trading pair symbol
            side: Trade side ('LONG' or 'SHORT')
            quantity: Trade quantity
            price: Trade price
        """
        try:
            position = Position.get_by_symbol(db, symbol)

            # Convert side to signed quantity
            signed_quantity = quantity if side == 'LONG' else -quantity

            if position:
                # Update existing position
                position.add_to_position(signed_quantity, price)

                # If position is closed (size = 0), remove it
                if position.size == 0:
                    db.delete(position)
                    logger.info(f"Position closed for {symbol}")
                else:
                    logger.info(f"Position updated for {symbol}",
                                new_size=str(position.size),
                                avg_entry=str(position.avg_entry))
            else:
                # Create new position
                position = Position(
                    symbol=symbol,
                    size=signed_quantity,
                    avg_entry=price,
                    leverage=1
                )
                db.add(position)
                logger.info(f"New position created for {symbol}",
                            size=str(signed_quantity), entry=str(price))

            db.commit()

        except Exception as e:
            logger.error(f"Error updating position",
                         symbol=symbol, error=str(e))
            db.rollback()

    def close_trade(self, db: Session, trade_id: int, exit_price: Decimal = None) -> bool:
        """
        Close an open trade.

        Args:
            db: Database session
            trade_id: Trade ID to close
            exit_price: Exit price (if None, uses current market price)

        Returns:
            True if closed successfully, False otherwise
        """
        try:
            trade = db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade or trade.status != 'OPEN':
                logger.warning(f"Trade {trade_id} not found or not open")
                return False

            # Get exit price
            if exit_price is None:
                exit_price = self.binance_client.get_ticker_price(trade.symbol)
                if not exit_price:
                    logger.error(
                        f"Failed to get current price for {trade.symbol}")
                    return False

            # Calculate PnL
            entry_price = Decimal(str(trade.entry_price))
            quantity = Decimal(str(trade.quantity))

            if trade.side == 'LONG':
                pnl = (exit_price - entry_price) * quantity
                binance_side = 'SELL'  # Close long position by selling
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
                binance_side = 'BUY'   # Close short position by buying

            # Place closing order
            order_response = self.binance_client.place_market_order(
                trade.symbol, binance_side, quantity
            )
            if not order_response:
                logger.error(
                    f"Failed to place closing order for trade {trade_id}")
                return False

            # Update trade record
            trade.status = 'CLOSED'
            trade.pnl = pnl
            trade.closed_at = datetime.utcnow()

            # Update position
            close_side = 'SHORT' if trade.side == 'LONG' else 'LONG'
            self.update_position(
                db, trade.symbol, close_side, quantity, exit_price)

            db.commit()

            logger.info(f"Trade closed successfully",
                        trade_id=trade_id, exit_price=str(exit_price),
                        pnl=str(pnl))

            return True

        except Exception as e:
            logger.error(f"Error closing trade",
                         trade_id=trade_id, error=str(e))
            db.rollback()
            return False


# Celery tasks

@celery_app.task(bind=True, max_retries=3)
def process_trading_signals(self):
    """Process high-score trading signals and execute trades."""
    try:
        db = next(get_db())
        executor = TradeExecutor()

        # Get unprocessed tweets with high signal scores
        high_score_tweets = (
            db.query(Tweet)
            .filter(
                Tweet.processed == True,
                Tweet.signal_score >= settings.trading.signal_threshold,
                Tweet.id.notin_(
                    db.query(Trade.tweet_id).filter(Trade.tweet_id.isnot(None))
                )
            )
            .order_by(Tweet.created_at.desc())
            .limit(10)  # Process up to 10 signals at a time
            .all()
        )

        if not high_score_tweets:
            logger.info("No high-score trading signals found")
            return {"processed": 0}

        processed_count = 0

        for tweet in high_score_tweets:
            try:
                # Determine trading symbol and side based on tweet content
                # For now, default to BTCUSDT and LONG (this can be enhanced with better NLP)
                symbol = "BTCUSDT"
                side = "LONG"  # Could be determined by sentiment analysis

                # Execute trade
                trade = executor.execute_trade_signal(
                    db, tweet.id, symbol, side)
                if trade:
                    processed_count += 1
                    logger.info(f"Trade executed for tweet {tweet.id}")
                else:
                    logger.warning(
                        f"Failed to execute trade for tweet {tweet.id}")

            except Exception as e:
                logger.error(
                    f"Error processing tweet {tweet.id}", error=str(e))
                continue

        logger.info(f"Processed trading signals",
                    total_signals=len(high_score_tweets),
                    executed_trades=processed_count)

        return {"processed": processed_count, "total_signals": len(high_score_tweets)}

    except Exception as e:
        logger.error(f"Error in process_trading_signals task", error=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(bind=True, max_retries=3)
def monitor_open_positions(self):
    """Monitor open positions for stop-loss and take-profit triggers."""
    try:
        db = next(get_db())
        executor = TradeExecutor()

        # Get all open trades
        open_trades = Trade.get_open_trades(db)

        if not open_trades:
            logger.info("No open trades to monitor")
            return {"monitored": 0, "closed": 0}

        closed_count = 0

        for trade in open_trades:
            try:
                # Get current market price
                current_price = executor.binance_client.get_ticker_price(
                    trade.symbol)
                if not current_price:
                    logger.warning(f"Failed to get price for {trade.symbol}")
                    continue

                should_close = False
                close_reason = ""

                # Check stop-loss
                if trade.stop_loss:
                    stop_loss = Decimal(str(trade.stop_loss))
                    if trade.side == 'LONG' and current_price <= stop_loss:
                        should_close = True
                        close_reason = "stop-loss"
                    elif trade.side == 'SHORT' and current_price >= stop_loss:
                        should_close = True
                        close_reason = "stop-loss"

                # Check take-profit
                if not should_close and trade.take_profit:
                    take_profit = Decimal(str(trade.take_profit))
                    if trade.side == 'LONG' and current_price >= take_profit:
                        should_close = True
                        close_reason = "take-profit"
                    elif trade.side == 'SHORT' and current_price <= take_profit:
                        should_close = True
                        close_reason = "take-profit"

                # Close trade if triggered
                if should_close:
                    if executor.close_trade(db, trade.id, current_price):
                        closed_count += 1
                        logger.info(
                            f"Trade {trade.id} closed due to {close_reason}")
                    else:
                        logger.error(f"Failed to close trade {trade.id}")

            except Exception as e:
                logger.error(
                    f"Error monitoring trade {trade.id}", error=str(e))
                continue

        logger.info(f"Position monitoring completed",
                    monitored=len(open_trades), closed=closed_count)

        return {"monitored": len(open_trades), "closed": closed_count}

    except Exception as e:
        logger.error(f"Error in monitor_open_positions task", error=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(bind=True, max_retries=3)
def update_position_pnl(self):
    """Update unrealized PnL for all open positions."""
    try:
        db = next(get_db())
        binance_client = BinanceClient()

        # Get all positions
        positions = Position.get_all_positions(db)

        if not positions:
            logger.info("No positions to update")
            return {"updated": 0}

        updated_count = 0

        for position in positions:
            try:
                # Get current market price
                current_price = binance_client.get_ticker_price(
                    position.symbol)
                if not current_price:
                    logger.warning(
                        f"Failed to get price for {position.symbol}")
                    continue

                # Update unrealized PnL
                Position.update_pnl_for_symbol(
                    db, position.symbol, current_price)
                updated_count += 1

            except Exception as e:
                logger.error(
                    f"Error updating PnL for {position.symbol}", error=str(e))
                continue

        logger.info(f"Position PnL update completed", updated=updated_count)

        return {"updated": updated_count}

    except Exception as e:
        logger.error(f"Error in update_position_pnl task", error=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(bind=True, max_retries=3)
def cleanup_pending_trades(self):
    """Clean up old pending trades (runs daily)."""
    try:
        cleaned_count = risk_manager.cleanup_old_pending_trades(hours=24)
        logger.info(f"Pending trades cleanup completed", cleaned=cleaned_count)
        return {"cleaned": cleaned_count}
    except Exception as e:
        logger.error(f"Error in cleanup_pending_trades task", error=str(e))
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
