#!/usr/bin/env python3
"""Test script for NLP processing functionality."""


import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from workers.nlp_processor import (
    calculate_keyword_score,
    analyze_sentiment,
    calculate_signal_score,
    get_sentiment_pipeline
)

def test_keyword_matching():
    """Test keyword matching functionality."""
    print("Testing keyword matching...")

    test_cases = [
        ("Bitcoin is going to the moon! 🚀", "High crypto relevance"),
        ("Just bought some ETH and BTC", "Multiple crypto mentions"),
        ("The weather is nice today", "No crypto relevance"),
        ("Bullish on Solana and DeFi projects", "Crypto trading terms"),
        ("This is an amazing breakthrough in blockchain technology", "Blockchain mention"),
    ]

    for text, description in test_cases:
        keyword_score, matched_keywords = calculate_keyword_score(text)
        print(f"\nText: {text}")
        print(f"Description: {description}")
        print(f"Keyword Score: {keyword_score}")
        print(f"Matched Keywords: {matched_keywords}")


def test_sentiment_analysis():
    """Test sentiment analysis functionality."""
    print("\n" + "="*50)
    print("Testing sentiment analysis...")

    test_cases = [
        ("Bitcoin is amazing! Going to the moon! 🚀", "Very positive"),
        ("This crypto crash is terrible, lost everything", "Very negative"),
        ("Bitcoin price is stable today", "Neutral"),
        ("Extremely bullish on Ethereum right now!", "Positive with amplifier"),
        ("Absolutely terrible market conditions", "Negative with amplifier"),
    ]

    for text, description in test_cases:
        sentiment_scores = analyze_sentiment(text)
        print(f"\nText: {text}")
        print(f"Description: {description}")
        print(f"Sentiment Scores: {sentiment_scores}")


def test_signal_calculation():
    """Test signal score calculation."""
    print("\n" + "="*50)
    print("Testing signal score calculation...")

    test_cases = [
        {
            "text": "Bitcoin is going to the moon! Extremely bullish! 🚀",
            "description": "High crypto relevance + very positive sentiment"
        },
        {
            "text": "This crypto crash is absolutely terrible",
            "description": "High crypto relevance + very negative sentiment"
        },
        {
            "text": "Bitcoin price is stable today",
            "description": "High crypto relevance + neutral sentiment"
        },
        {
            "text": "The weather is nice today",
            "description": "No crypto relevance"
        },
        {
            "text": "Just bought ETH, SOL, and BTC. Very excited!",
            "description": "Multiple high-value cryptos + positive sentiment"
        }
    ]

    for case in test_cases:
        text = case["text"]
        description = case["description"]

        # Calculate components
        keyword_score, matched_keywords = calculate_keyword_score(text)
        sentiment_scores = analyze_sentiment(text)
        signal_score = calculate_signal_score(
            keyword_score, sentiment_scores, matched_keywords)

        print(f"\nText: {text}")
        print(f"Description: {description}")
        print(f"Keyword Score: {keyword_score}")
        print(f"Matched Keywords: {matched_keywords}")
        print(f"Sentiment Scores: {sentiment_scores}")
        print(f"Final Signal Score: {signal_score}")


def test_model_loading():
    """Test that the sentiment model loads correctly."""
    print("\n" + "="*50)
    print("Testing model loading...")

    try:
        pipeline = get_sentiment_pipeline()
        print("✓ Sentiment model loaded successfully")

        # Test a simple prediction
        test_text = "This is a test"
        result = pipeline(test_text)
        print(f"✓ Model prediction works: {result}")

    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print("NLP Processing Test Suite")
    print("=" * 50)

    # Test individual components
    test_keyword_matching()
    test_sentiment_analysis()
    test_signal_calculation()

    # Test model loading (this will download the model if not cached)
    print("\nTesting model loading (this may take a while on first run)...")
    model_loaded = test_model_loading()

    if model_loaded:
        print("\n✓ All tests completed successfully!")
    else:
        print("\n✗ Some tests failed. Check the output above.")
