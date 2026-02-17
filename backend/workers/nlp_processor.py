"""NLP processing worker for tweet sentiment analysis and signal generation."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from celery import Task
from sqlalchemy.orm import Session
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from workers.celery_app import celery_app
from app.database import get_db
from app.models.tweet import Tweet
from app.monitoring.metrics import tweets_processed, worker_task_duration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model caching
_sentiment_pipeline = None
_tokenizer = None
_model = None

# Crypto-related keywords with weights
CRYPTO_KEYWORDS = {
    # Major cryptocurrencies (high weight)
    'bitcoin': 3, 'btc': 3, 'ethereum': 3, 'eth': 3, 'solana': 3, 'sol': 3,
    'cardano': 3, 'ada': 3, 'polkadot': 3, 'dot': 3, 'chainlink': 3, 'link': 3,
    'polygon': 3, 'matic': 3, 'avalanche': 3, 'avax': 3, 'cosmos': 3, 'atom': 3,

    # Trading terms (medium weight)
    'crypto': 2, 'cryptocurrency': 2, 'blockchain': 2, 'defi': 2, 'nft': 2,
    'altcoin': 2, 'hodl': 2, 'moon': 2, 'lambo': 2, 'diamond hands': 2,
    'paper hands': 2, 'bull market': 2, 'bear market': 2, 'pump': 2, 'dump': 2,
    'dip': 2, 'ath': 2, 'all time high': 2, 'market cap': 2, 'volume': 2,

    # General terms (low weight)
    'trading': 1, 'investment': 1, 'portfolio': 1, 'profit': 1, 'loss': 1,
    'buy': 1, 'sell': 1, 'hold': 1, 'long': 1, 'short': 1, 'bullish': 1,
    'bearish': 1, 'resistance': 1, 'support': 1, 'breakout': 1, 'correction': 1,

    # Exchanges and platforms (medium weight)
    'binance': 2, 'coinbase': 2, 'kraken': 2, 'ftx': 2, 'uniswap': 2,
    'pancakeswap': 2, 'metamask': 2, 'ledger': 2, 'trezor': 2,

    # Technical analysis (low weight)
    'rsi': 1, 'macd': 1, 'fibonacci': 1, 'candlestick': 1, 'chart': 1,
    'technical analysis': 1, 'ta': 1, 'pattern': 1, 'trend': 1,
}

# Sentiment modifiers that can amplify signals
SENTIMENT_AMPLIFIERS = {
    'extremely': 1.5, 'very': 1.3, 'really': 1.2, 'absolutely': 1.4,
    'definitely': 1.3, 'certainly': 1.2, 'massive': 1.4, 'huge': 1.3,
    'incredible': 1.3, 'amazing': 1.2, 'terrible': 1.3, 'awful': 1.2,
    'disaster': 1.4, 'crash': 1.3, 'explode': 1.3, 'rocket': 1.2,
}


def get_sentiment_pipeline():
    """Get or initialize the sentiment analysis pipeline."""
    global _sentiment_pipeline, _tokenizer, _model

    if _sentiment_pipeline is None:
        try:
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            logger.info(f"Loading sentiment model: {model_name}")

            # Load tokenizer and model
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModelForSequenceClassification.from_pretrained(
                model_name)

            # Create pipeline
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=_model,
                tokenizer=_tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                return_all_scores=True
            )

            logger.info("Sentiment model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise

    return _sentiment_pipeline


def calculate_keyword_score(text: str) -> Tuple[float, List[str]]:
    """
    Calculate keyword relevance score for crypto-related terms.

    Args:
        text: Tweet text to analyze

    Returns:
        Tuple of (keyword_score, matched_keywords)
        keyword_score: 0-100 score based on keyword matches
        matched_keywords: List of matched keywords
    """
    text_lower = text.lower()
    matched_keywords = []
    total_weight = 0

    # Check for keyword matches
    for keyword, weight in CRYPTO_KEYWORDS.items():
        # Use word boundaries for exact matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            matched_keywords.append(keyword)
            total_weight += weight

    # Apply sentiment amplifiers
    amplifier_bonus = 0
    for amplifier, multiplier in SENTIMENT_AMPLIFIERS.items():
        pattern = r'\b' + re.escape(amplifier) + r'\b'
        if re.search(pattern, text_lower):
            amplifier_bonus += (multiplier - 1) * 10  # Convert to bonus points

    # Calculate base score (0-50 range for keywords)
    keyword_score = min(total_weight * 5, 50)  # Cap at 50

    # Add amplifier bonus (up to 20 points)
    keyword_score += min(amplifier_bonus, 20)

    # Ensure score is in 0-100 range
    keyword_score = max(0, min(keyword_score, 100))

    return keyword_score, matched_keywords


def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of tweet text using Hugging Face model.

    Args:
        text: Tweet text to analyze

    Returns:
        Dictionary with sentiment scores
    """
    try:
        pipeline = get_sentiment_pipeline()

        # Truncate text if too long (RoBERTa has 512 token limit)
        if len(text) > 400:  # Conservative limit to account for tokenization
            text = text[:400] + "..."

        # Get sentiment predictions
        results = pipeline(text)[0]  # Get first (and only) result

        # Convert to standardized format
        sentiment_scores = {}
        for result in results:
            label = result['label'].lower()
            score = result['score']

            # Map labels to standardized names
            if label in ['positive', 'pos']:
                sentiment_scores['positive'] = score
            elif label in ['negative', 'neg']:
                sentiment_scores['negative'] = score
            elif label in ['neutral']:
                sentiment_scores['neutral'] = score

        return sentiment_scores

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        # Return neutral sentiment on error
        return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}


def calculate_signal_score(keyword_score: float, sentiment_scores: Dict[str, float],
                           matched_keywords: List[str]) -> int:
    """
    Calculate combined signal score from keyword and sentiment analysis.

    Args:
        keyword_score: Keyword relevance score (0-100)
        sentiment_scores: Sentiment analysis results
        matched_keywords: List of matched crypto keywords

    Returns:
        Combined signal score (0-100)
    """
    # If no crypto keywords matched, return low score
    if not matched_keywords or keyword_score == 0:
        return 0

    # Calculate sentiment component (-1 to 1 scale)
    positive_score = sentiment_scores.get('positive', 0)
    negative_score = sentiment_scores.get('negative', 0)
    neutral_score = sentiment_scores.get('neutral', 0)

    # Convert to sentiment polarity (-1 to 1)
    sentiment_polarity = positive_score - negative_score

    # Keyword score contributes 60% of final score
    keyword_component = keyword_score * 0.6

    # Sentiment contributes 40% of final score
    # Strong positive/negative sentiment gets higher weight than neutral
    sentiment_strength = max(positive_score, negative_score)
    sentiment_component = sentiment_strength * abs(sentiment_polarity) * 40

    # Combine components
    signal_score = keyword_component + sentiment_component

    # Apply bonuses for high-value keywords
    high_value_keywords = ['bitcoin', 'btc',
                           'ethereum', 'eth', 'solana', 'sol']
    if any(keyword in matched_keywords for keyword in high_value_keywords):
        signal_score *= 1.1  # 10% bonus

    # Ensure score is in 0-100 range
    signal_score = max(0, min(int(signal_score), 100))

    return signal_score


@celery_app.task(bind=True, max_retries=3)
def analyze_tweet_sentiment(self: Task, tweet_id: int) -> Dict[str, any]:
    """
    Analyze sentiment and calculate signal score for a single tweet.

    Args:
        tweet_id: ID of tweet to analyze

    Returns:
        Dictionary with analysis results
    """
    db = next(get_db())

    try:
        # Get tweet from database
        tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
        if not tweet:
            logger.error(f"Tweet {tweet_id} not found")
            return {"error": "Tweet not found"}

        if tweet.processed:
            logger.info(f"Tweet {tweet_id} already processed")
            return {"message": "Tweet already processed", "signal_score": tweet.signal_score}

        logger.info(f"Analyzing tweet {tweet_id} from @{tweet.author}")

        # Calculate keyword score
        keyword_score, matched_keywords = calculate_keyword_score(tweet.text)

        # Analyze sentiment
        sentiment_scores = analyze_sentiment(tweet.text)

        # Calculate combined signal score
        signal_score = calculate_signal_score(
            keyword_score, sentiment_scores, matched_keywords)

        # Convert sentiment to single score for database storage
        sentiment_polarity = sentiment_scores.get(
            'positive', 0) - sentiment_scores.get('negative', 0)

        # Update tweet with results
        success = tweet.mark_processed(db, sentiment_polarity, signal_score)

        if success:
            logger.info(f"Tweet {tweet_id} processed: signal_score={signal_score}, "
                        f"sentiment={sentiment_polarity:.3f}, keywords={len(matched_keywords)}")

            return {
                "tweet_id": tweet_id,
                "signal_score": signal_score,
                "sentiment_score": sentiment_polarity,
                "keyword_score": keyword_score,
                "matched_keywords": matched_keywords,
                "sentiment_breakdown": sentiment_scores
            }
        else:
            logger.error(f"Failed to update tweet {tweet_id} in database")
            return {"error": "Database update failed"}

    except Exception as exc:
        logger.error(f"Error analyzing tweet {tweet_id}: {exc}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 2 ** self.request.retries
            logger.info(
                f"Retrying tweet {tweet_id} analysis in {retry_delay} seconds")
            raise self.retry(exc=exc, countdown=retry_delay)

        return {"error": str(exc)}

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_unprocessed_tweets(self: Task, limit: int = 50) -> Dict[str, any]:
    """
    Process batch of unprocessed tweets for sentiment analysis.

    Args:
        limit: Maximum number of tweets to process

    Returns:
        Dictionary with processing results
    """
    with worker_task_duration.labels(task_name='process_unprocessed_tweets').time():
        db = next(get_db())

        try:
            # Get unprocessed tweets
            unprocessed_tweets = Tweet.get_unprocessed(db, limit=limit)

            if not unprocessed_tweets:
                logger.info("No unprocessed tweets found")
                return {"message": "No unprocessed tweets", "processed_count": 0}

            logger.info(f"Processing {len(unprocessed_tweets)} unprocessed tweets")

            processed_count = 0
            high_signal_count = 0
            errors = []

            # Process each tweet
            for tweet in unprocessed_tweets:
                try:
                    # Analyze tweet
                    result = analyze_tweet_sentiment.apply(args=[tweet.id]).get()

                    if "error" not in result:
                        processed_count += 1
                        if result.get("signal_score", 0) >= 70:
                            high_signal_count += 1
                            logger.info(f"High signal tweet detected: {tweet.id} "
                                        f"(score: {result['signal_score']})")
                    else:
                        errors.append(f"Tweet {tweet.id}: {result['error']}")

                except Exception as e:
                    error_msg = f"Tweet {tweet.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Error processing tweet {tweet.id}: {e}")

            # Update metrics
            tweets_processed.inc(processed_count)

            logger.info(f"Batch processing complete: {processed_count}/{len(unprocessed_tweets)} "
                        f"processed, {high_signal_count} high signals")

            return {
                "total_tweets": len(unprocessed_tweets),
                "processed_count": processed_count,
                "high_signal_count": high_signal_count,
                "errors": errors
            }

        except Exception as exc:
            logger.error(f"Error in batch processing: {exc}")

            # Retry with exponential backoff
            if self.request.retries < self.max_retries:
                retry_delay = 2 ** self.request.retries
                logger.info(f"Retrying batch processing in {retry_delay} seconds")
                raise self.retry(exc=exc, countdown=retry_delay)

            return {"error": str(exc)}

        finally:
            db.close()


@celery_app.task
def get_processing_stats() -> Dict[str, any]:
    """
    Get statistics about tweet processing status.

    Returns:
        Dictionary with processing statistics
    """
    db = next(get_db())

    try:
        # Count tweets by processing status
        total_tweets = db.query(Tweet).count()
        processed_tweets = db.query(Tweet).filter(
            Tweet.processed == True).count()
        unprocessed_tweets = db.query(Tweet).filter(
            Tweet.processed == False).count()

        # Count high signal tweets
        high_signal_tweets = db.query(Tweet).filter(
            Tweet.signal_score >= 70,
            Tweet.processed == True
        ).count()

        # Get recent processing activity (last 24 hours)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_processed = db.query(Tweet).filter(
            Tweet.processed == True,
            Tweet.created_at_db >= recent_cutoff
        ).count()

        return {
            "total_tweets": total_tweets,
            "processed_tweets": processed_tweets,
            "unprocessed_tweets": unprocessed_tweets,
            "high_signal_tweets": high_signal_tweets,
            "recent_processed_24h": recent_processed,
            "processing_rate": round(processed_tweets / max(total_tweets, 1) * 100, 2)
        }

    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return {"error": str(e)}

    finally:
        db.close()
