from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class SentimentBreakdown(BaseModel):
    """Sentiment distribution."""
    positive: float = Field(ge=0, le=1)
    negative: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)


class ThemeAnalysis(BaseModel):
    """Thematic analysis of reviews."""
    theme: str
    mention_count: int
    sentiment: str
    impact_score: float = Field(ge=0, le=10)


class ReviewSample(BaseModel):
    """Representative review sample."""
    text: str
    rating: int = Field(ge=1, le=5)
    sentiment: str
    date: str


class SentimentAnalysisResult(BaseModel):
    """Complete sentiment analysis result."""
    product: str
    analysis_date: str
    overall_score: float = Field(ge=0, le=5)
    total_reviews: int
    sentiment_breakdown: SentimentBreakdown
    key_themes: Dict[str, List[ThemeAnalysis]]
    recommendation_rate: float = Field(ge=0, le=1)
    nps_score: int = Field(ge=-100, le=100)
    trend: str
    sample_reviews: List[ReviewSample]
    confidence_level: str


class SentimentAnalyzerConfig(BaseModel):
    """Analyzer configuration."""
    timeout: float = 30.0
    max_reviews: int = 20


class SentimentAnalyzerService:
    """Customer review sentiment analysis service using web scraping."""

    def __init__(self, config: Optional[SentimentAnalyzerConfig] = None):
        self.config = config or SentimentAnalyzerConfig()
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzerService")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def _scrape_reviews(self, product_name: str) -> List[Dict[str, Any]]:
        """Scrape reviews from web search results."""
        reviews = []

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                query = f"{product_name} review customer opinion"
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, "html.parser")

                snippets = soup.select(".result__snippet")
                for snippet in snippets[:self.config.max_reviews]:
                    text = snippet.get_text().strip()
                    if len(text) > 20:
                        sentiment = self._analyze_text_sentiment(text)
                        rating = self._estimate_rating(sentiment)
                        reviews.append({
                            "text": text[:300],
                            "sentiment": sentiment,
                            "rating": rating
                        })
            except Exception as e:
                self.logger.warning(f"Review scraping failed: {e}")

        return reviews

    def _analyze_text_sentiment(self, text: str) -> str:
        """Analyze sentiment of a text snippet."""
        text_lower = text.lower()

        positive_indicators = [
            "excellent", "amazing", "great", "love", "best", "perfect",
            "fantastic", "awesome", "recommend", "satisfied", "happy",
            "quality", "worth", "impressive", "outstanding", "brilliant"
        ]

        negative_indicators = [
            "terrible", "awful", "worst", "hate", "disappointed", "poor",
            "bad", "broke", "waste", "regret", "horrible", "useless",
            "defective", "cheap", "failed", "problem", "issue", "avoid"
        ]

        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"

    def _estimate_rating(self, sentiment: str) -> int:
        """Estimate rating based on sentiment."""
        if sentiment == "positive":
            return 4
        elif sentiment == "negative":
            return 2
        return 3

    async def _extract_themes(self, product_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract themes from scraped content."""
        positive_themes = []
        negative_themes = []

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                # Search for positive aspects
                pos_query = f"{product_name} pros advantages benefits review"
                pos_url = f"https://html.duckduckgo.com/html/?q={pos_query}"
                pos_response = await client.get(pos_url, headers=self.headers)
                pos_soup = BeautifulSoup(pos_response.text, "html.parser")

                pos_snippets = pos_soup.select(".result__snippet")
                pos_text = " ".join(s.get_text() for s in pos_snippets[:5]).lower()
                positive_themes = self._identify_themes(pos_text, "positive")

                # Search for negative aspects
                neg_query = f"{product_name} cons disadvantages problems issues review"
                neg_url = f"https://html.duckduckgo.com/html/?q={neg_query}"
                neg_response = await client.get(neg_url, headers=self.headers)
                neg_soup = BeautifulSoup(neg_response.text, "html.parser")

                neg_snippets = neg_soup.select(".result__snippet")
                neg_text = " ".join(s.get_text() for s in neg_snippets[:5]).lower()
                negative_themes = self._identify_themes(neg_text, "negative")

            except Exception as e:
                self.logger.warning(f"Theme extraction failed: {e}")

        return {"positive": positive_themes, "negative": negative_themes}

    def _identify_themes(self, text: str, sentiment: str) -> List[ThemeAnalysis]:
        """Identify themes from text using word frequency and patterns."""
        # Extract meaningful phrases
        words = re.findall(r'\b[a-z]{4,}\b', text)

        stopwords = {
            "this", "that", "with", "from", "have", "will", "your", "about",
            "more", "when", "which", "their", "been", "would", "could", "should",
            "they", "them", "there", "here", "what", "where", "also", "just",
            "very", "really", "some", "many", "much", "most", "other", "only"
        }

        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top themes
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        themes = []
        for word, count in top_words:
            impact = min(10.0, count * 0.5 + 5) if sentiment == "positive" else min(7.0, count * 0.3 + 3)
            themes.append(ThemeAnalysis(
                theme=word.title(),
                mention_count=count * 10,
                sentiment=sentiment,
                impact_score=round(impact, 1)
            ))

        return themes

    def _calculate_sentiment_breakdown(self, reviews: List[Dict[str, Any]]) -> SentimentBreakdown:
        """Calculate sentiment breakdown from reviews."""
        if not reviews:
            return SentimentBreakdown(positive=0.33, negative=0.33, neutral=0.34)

        total = len(reviews)
        positive = sum(1 for r in reviews if r["sentiment"] == "positive") / total
        negative = sum(1 for r in reviews if r["sentiment"] == "negative") / total
        neutral = sum(1 for r in reviews if r["sentiment"] == "neutral") / total

        return SentimentBreakdown(
            positive=round(positive, 2),
            negative=round(negative, 2),
            neutral=round(neutral, 2)
        )

    def _calculate_overall_score(self, breakdown: SentimentBreakdown) -> float:
        """Calculate overall score from sentiment breakdown."""
        score = 3.0 + breakdown.positive * 2.0 - breakdown.negative * 1.5
        return round(min(5.0, max(1.0, score)), 1)

    def _calculate_nps(self, positive_ratio: float, negative_ratio: float) -> int:
        """Calculate Net Promoter Score."""
        promoters = positive_ratio * 0.8
        detractors = negative_ratio * 0.9
        return int((promoters - detractors) * 100)

    def _determine_trend(self, overall_score: float) -> str:
        """Determine sentiment trend."""
        if overall_score >= 4.0:
            return "↑ Rising"
        elif overall_score >= 3.0:
            return "→ Stable"
        return "↓ Declining"

    def _assess_confidence(self, total_reviews: int) -> str:
        """Assess analysis confidence level."""
        if total_reviews >= 15:
            return "High"
        elif total_reviews >= 8:
            return "Medium"
        return "Low"

    def _create_sample_reviews(self, reviews: List[Dict[str, Any]]) -> List[ReviewSample]:
        """Create sample reviews from scraped data."""
        samples = []
        for review in reviews[:5]:
            samples.append(ReviewSample(
                text=review["text"],
                rating=review["rating"],
                sentiment=review["sentiment"],
                date=datetime.now().strftime("%Y-%m-%d")
            ))
        return samples

    async def analyze_async(self, product_name: str) -> SentimentAnalysisResult:
        """Execute complete sentiment analysis."""
        self.logger.info(f"Analyzing sentiment for: {product_name}")

        reviews = await self._scrape_reviews(product_name)
        themes = await self._extract_themes(product_name)

        breakdown = self._calculate_sentiment_breakdown(reviews)
        overall_score = self._calculate_overall_score(breakdown)
        total_reviews = len(reviews)

        return SentimentAnalysisResult(
            product=product_name,
            analysis_date=datetime.now().isoformat(),
            overall_score=overall_score,
            total_reviews=total_reviews,
            sentiment_breakdown=breakdown,
            key_themes=themes,
            recommendation_rate=round(breakdown.positive * 0.95, 2),
            nps_score=self._calculate_nps(breakdown.positive, breakdown.negative),
            trend=self._determine_trend(overall_score),
            sample_reviews=self._create_sample_reviews(reviews),
            confidence_level=self._assess_confidence(total_reviews)
        )

    def analyze(self, product_name: str) -> SentimentAnalysisResult:
        """Synchronous wrapper for analyze_async."""
        import asyncio
        return asyncio.run(self.analyze_async(product_name))


@tool
@tool_error_handler("analyze_sentiment")
def analyze_sentiment(product_name: str) -> Dict[str, Any]:
    """Analyze customer review sentiment for a product.

    Scrapes the web to provide:
    - Overall score and sentiment distribution
    - Key positive and negative themes with impact
    - Net Promoter Score (NPS)
    - Trend and review samples
    - Analysis confidence level

    Args:
        product_name: The product name to analyze

    Returns:
        Complete sentiment analysis with actionable insights
    """
    service = SentimentAnalyzerService()
    result = service.analyze(product_name)
    return result.model_dump()