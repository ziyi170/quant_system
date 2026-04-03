"""
NLP-based sentiment analysis for market news and social sentiment.
Uses HuggingFace transformers for state-of-the-art NLP.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    label: str  # POSITIVE, NEGATIVE, NEUTRAL
    score: float  # 0-1, confidence
    sentiment_value: float  # -1 to +1 for continuous scoring


class SentimentAnalyzer:
    """
    Sentiment analysis using HuggingFace transformers.
    
    Models available:
    - distilbert-base-uncased-finetuned-sst-2-english (fast, accurate)
    - bert-base-uncased + sentiment fine-tuning
    - RoBERTa fine-tuned models
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """Initialize sentiment analyzer"""
        try:
            from transformers import pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=-1  # CPU mode (change to 0 for GPU)
            )
            logger.info(f"✅ Loaded sentiment model: {model_name}")
        except ImportError:
            logger.error("❌ transformers library not installed. Install: pip install transformers")
            self.pipeline = None
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of a text.
        
        Args:
            text: Text to analyze (news headline, tweet, etc.)
        
        Returns:
            SentimentResult with label and score
        """
        if not self.pipeline:
            logger.warning("Sentiment analyzer not initialized")
            return SentimentResult(text, "NEUTRAL", 0.5, 0.0)
        
        try:
            # Truncate long texts to avoid transformer limits
            text = text[:512]
            
            result = self.pipeline(text)[0]
            label = result['label']  # POSITIVE or NEGATIVE
            score = result['score']  # 0-1 confidence
            
            # Convert to continuous -1 to +1 scale
            if label == "POSITIVE":
                sentiment_value = score  # 0 to 1
            else:  # NEGATIVE
                sentiment_value = -score  # -1 to 0
            
            return SentimentResult(
                text=text,
                label=label,
                score=score,
                sentiment_value=sentiment_value
            )
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return SentimentResult(text, "NEUTRAL", 0.5, 0.0)
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment for multiple texts"""
        return [self.analyze(text) for text in texts]
    
    def get_aggregate_sentiment(self, texts: List[str]) -> Dict:
        """Get aggregated sentiment across multiple texts"""
        results = self.analyze_batch(texts)
        
        scores = [r.sentiment_value for r in results]
        labels = [r.label for r in results]
        
        return {
            "average_sentiment": np.mean(scores),
            "std_sentiment": np.std(scores),
            "positive_count": labels.count("POSITIVE"),
            "negative_count": labels.count("NEGATIVE"),
            "positive_ratio": labels.count("POSITIVE") / len(labels) if labels else 0,
            "overall_label": "POSITIVE" if np.mean(scores) > 0.1 else "NEGATIVE" if np.mean(scores) < -0.1 else "NEUTRAL"
        }


class FinancialNewsSentimentAnalyzer:
    """
    Specialized sentiment analyzer for financial news.
    
    Includes domain-specific terms and financial terminology.
    """
    
    # Financial sentiment keywords
    POSITIVE_KEYWORDS = {
        "beat", "outperform", "surge", "rally", "gains", "strong",
        "bullish", "above expectations", "exceed", "upgrade", "buy",
        "breakout", "momentum", "positive", "growth", "profit",
        "earnings beat", "guidance raise", "record", "new high"
    }
    
    NEGATIVE_KEYWORDS = {
        "miss", "underperform", "plunge", "decline", "loses", "weak",
        "bearish", "below expectations", "miss", "downgrade", "sell",
        "breakdown", "negative", "loss", "decline", "bankruptcy",
        "earnings miss", "guidance cut", "layoff", "weakness"
    }
    
    def __init__(self):
        self.base_analyzer = SentimentAnalyzer()
    
    def analyze_financial_news(self, headline: str, body: Optional[str] = None) -> Dict:
        """
        Analyze financial news with domain-specific logic.
        
        Args:
            headline: News headline
            body: Optional news body text
        
        Returns:
            Detailed sentiment analysis with financial signals
        """
        # Combine headline and body
        full_text = headline + " " + (body or "")
        
        # Get base sentiment
        base_result = self.base_analyzer.analyze(full_text)
        
        # Check for financial keywords
        text_lower = full_text.lower()
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        
        # Adjust sentiment based on keywords
        keyword_adjustment = (positive_count - negative_count) * 0.1
        adjusted_sentiment = np.clip(base_result.sentiment_value + keyword_adjustment, -1, 1)
        
        return {
            "headline": headline,
            "base_sentiment": base_result.sentiment_value,
            "adjusted_sentiment": adjusted_sentiment,
            "confidence": base_result.score,
            "positive_keywords": positive_count,
            "negative_keywords": negative_count,
            "is_surprise": positive_count != negative_count,  # Unbalanced suggests surprise
            "market_impact": "HIGH" if abs(adjusted_sentiment) > 0.7 else "MEDIUM" if abs(adjusted_sentiment) > 0.4 else "LOW"
        }


class EventSentimentAggregator:
    """
    Aggregate sentiment from multiple sources for a stock/event.
    """
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.analyzer = FinancialNewsSentimentAnalyzer()
    
    def aggregate_stock_sentiment(
        self,
        symbol: str,
        news_items: List[Dict]
    ) -> Dict:
        """
        Aggregate sentiment for a stock from multiple news sources.
        
        Args:
            symbol: Stock symbol
            news_items: List of {headline, source, timestamp, body}
        
        Returns:
            Aggregated sentiment analysis
        """
        sentiments = []
        
        for item in news_items:
            analysis = self.analyzer.analyze_financial_news(
                item.get("headline", ""),
                item.get("body")
            )
            sentiments.append(analysis)
        
        if not sentiments:
            return {
                "symbol": symbol,
                "aggregate_sentiment": 0.0,
                "news_count": 0,
                "sentiment_distribution": {}
            }
        
        # Calculate aggregates
        sentiments_array = np.array([s["adjusted_sentiment"] for s in sentiments])
        
        return {
            "symbol": symbol,
            "aggregate_sentiment": np.mean(sentiments_array),
            "sentiment_std": np.std(sentiments_array),
            "news_count": len(sentiments),
            "positive_news": len([s for s in sentiments if s["adjusted_sentiment"] > 0.1]),
            "negative_news": len([s for s in sentiments if s["adjusted_sentiment"] < -0.1]),
            "sentiment_distribution": {
                "HIGH_POSITIVE": len([s for s in sentiments if s["adjusted_sentiment"] > 0.7]),
                "POSITIVE": len([s for s in sentiments if 0.1 < s["adjusted_sentiment"] <= 0.7]),
                "NEUTRAL": len([s for s in sentiments if -0.1 <= s["adjusted_sentiment"] <= 0.1]),
                "NEGATIVE": len([s for s in sentiments if -0.7 <= s["adjusted_sentiment"] < -0.1]),
                "HIGH_NEGATIVE": len([s for s in sentiments if s["adjusted_sentiment"] < -0.7])
            },
            "market_impact": "HIGH" if np.std(sentiments_array) > 0.3 else "MEDIUM" if np.std(sentiments_array) > 0.15 else "LOW"
        }


class SentimentSignalGenerator:
    """
    Convert sentiment scores to trading signals.
    """
    
    def __init__(
        self,
        positive_threshold: float = 0.6,
        negative_threshold: float = -0.6
    ):
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
    
    def generate_signal(self, sentiment_value: float) -> int:
        """
        Convert sentiment to signal.
        
        Returns:
            1 (buy), 0 (hold), -1 (sell)
        """
        if sentiment_value > self.positive_threshold:
            return 1  # Buy
        elif sentiment_value < self.negative_threshold:
            return -1  # Sell
        else:
            return 0  # Hold
    
    def generate_position_size(self, sentiment_value: float, max_size: float = 0.1) -> float:
        """
        Generate position size based on sentiment confidence.
        
        Args:
            sentiment_value: -1 to +1
            max_size: Maximum position size (default 10%)
        
        Returns:
            Position size as fraction of portfolio
        """
        confidence = abs(sentiment_value)  # 0-1
        return confidence * max_size


# Convenience functions
def analyze_news_sentiment(headlines: List[str]) -> Dict:
    """Quick sentiment analysis for news headlines"""
    analyzer = SentimentAnalyzer()
    results = analyzer.analyze_batch(headlines)
    
    return {
        "average_sentiment": np.mean([r.sentiment_value for r in results]),
        "positive_count": len([r for r in results if r.label == "POSITIVE"]),
        "negative_count": len([r for r in results if r.label == "NEGATIVE"]),
        "results": results
    }


def get_financial_sentiment(headline: str) -> Dict:
    """Quick financial sentiment analysis"""
    analyzer = FinancialNewsSentimentAnalyzer()
    return analyzer.analyze_financial_news(headline)
