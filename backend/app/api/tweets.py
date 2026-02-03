"""
Tweet API endpoints for retrieving tweet data and signals.

This module provides endpoints for:
- Recent tweets with signal scores
- Tweet filtering and pagination
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tweet import Tweet
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tweets", tags=["tweets"])


@router.get("/", response_model=List[dict])
async def get_recent_tweets(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200,
                       description="Number of tweets to return"),
    hours: int = Query(default=24, ge=1, le=168,
                       description="Hours to look back"),
    min_signal_score: Optional[int] = Query(
        default=None, ge=0, le=100, description="Minimum signal score filter"),
    author: Optional[str] = Query(
        default=None, description="Filter by tweet author"),
    processed_only: bool = Query(
        default=False, description="Only return processed tweets")
):
    """
    Get recent tweets with their signal scores.

    This endpoint retrieves tweets from the specified time window with optional filtering
    by signal score, author, and processing status.

    Args:
        db: Database session
        limit: Maximum number of tweets to return (1-200)
        hours: Number of hours to look back (1-168)
        min_signal_score: Minimum signal score threshold (0-100)
        author: Filter by specific tweet author
        processed_only: Only return tweets that have been processed for sentiment

    Returns:
        List of tweet dictionaries with metadata and signal scores

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching recent tweets",
                    limit=limit,
                    hours=hours,
                    min_signal_score=min_signal_score,
                    author=author,
                    processed_only=processed_only)

        # Start with recent tweets query
        if author:
            tweets = Tweet.get_by_author(db, author=author, limit=limit)
        elif min_signal_score is not None:
            tweets = Tweet.get_high_signals(
                db, min_signal_score=min_signal_score, limit=limit)
        else:
            tweets = Tweet.get_recent(db, hours=hours, limit=limit)

        # Apply processed filter if requested
        if processed_only:
            tweets = [tweet for tweet in tweets if tweet.processed]

        # Convert to dictionaries
        tweet_data = [tweet.to_dict() for tweet in tweets]

        logger.info("Successfully retrieved tweets", count=len(tweet_data))
        return tweet_data

    except Exception as e:
        logger.error("Failed to retrieve tweets", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve tweets"
        )


@router.get("/signals", response_model=List[dict])
async def get_high_signal_tweets(
    db: Session = Depends(get_db),
    min_signal_score: int = Query(
        default=70, ge=0, le=100, description="Minimum signal score"),
    limit: int = Query(default=20, ge=1, le=100,
                       description="Number of tweets to return")
):
    """
    Get tweets with high signal scores for trading opportunities.

    This endpoint specifically retrieves tweets that have strong trading signals
    based on sentiment analysis and keyword matching.

    Args:
        db: Database session
        min_signal_score: Minimum signal score threshold (default 70)
        limit: Maximum number of tweets to return (1-100)

    Returns:
        List of high-signal tweet dictionaries

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching high signal tweets",
                    min_signal_score=min_signal_score,
                    limit=limit)

        tweets = Tweet.get_high_signals(
            db, min_signal_score=min_signal_score, limit=limit)
        tweet_data = [tweet.to_dict() for tweet in tweets]

        logger.info("Successfully retrieved high signal tweets",
                    count=len(tweet_data))
        return tweet_data

    except Exception as e:
        logger.error("Failed to retrieve high signal tweets", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve high signal tweets"
        )


@router.get("/unprocessed", response_model=List[dict])
async def get_unprocessed_tweets(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200,
                       description="Number of tweets to return")
):
    """
    Get tweets that haven't been processed for sentiment analysis.

    This endpoint is primarily for monitoring and debugging the NLP processing pipeline.

    Args:
        db: Database session
        limit: Maximum number of tweets to return (1-200)

    Returns:
        List of unprocessed tweet dictionaries

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info("Fetching unprocessed tweets", limit=limit)

        tweets = Tweet.get_unprocessed(db, limit=limit)
        tweet_data = [tweet.to_dict() for tweet in tweets]

        logger.info("Successfully retrieved unprocessed tweets",
                    count=len(tweet_data))
        return tweet_data

    except Exception as e:
        logger.error("Failed to retrieve unprocessed tweets", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve unprocessed tweets"
        )


@router.get("/{tweet_id}", response_model=dict)
async def get_tweet_by_id(
    tweet_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific tweet by its ID.

    Args:
        tweet_id: Twitter tweet ID
        db: Database session

    Returns:
        Tweet dictionary with metadata and signal scores

    Raises:
        HTTPException: If tweet not found or database query fails
    """
    try:
        logger.info("Fetching tweet by ID", tweet_id=tweet_id)

        tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
        if not tweet:
            raise HTTPException(
                status_code=404,
                detail=f"Tweet with ID {tweet_id} not found"
            )

        tweet_data = tweet.to_dict()
        logger.info("Successfully retrieved tweet", tweet_id=tweet_id)
        return tweet_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve tweet",
                     tweet_id=tweet_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve tweet"
        )
