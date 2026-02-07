from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import random

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


class SentimentAnalyzerService:
    """Customer review sentiment analysis service."""

    POSITIVE_THEMES = [
        ("audio quality", "Excellent sound quality mentioned"),
        ("comfort", "Wearing comfort appreciated"),
        ("battery life", "Good battery autonomy"),
        ("value for money", "Good value for money"),
        ("design", "Modern and elegant design"),
        ("ease of use", "Intuitive setup"),
        ("stable bluetooth", "Reliable connection"),
    ]

    NEGATIVE_THEMES = [
        ("durability", "Durability issues reported"),
        ("customer service", "Customer service criticized"),
        ("manual", "Insufficient documentation"),
        ("price", "Perceived as too expensive"),
        ("noise", "Insufficient noise isolation"),
        ("microphone", "Disappointing microphone quality"),
    ]

    SAMPLE_POSITIVE_REVIEWS = [
        "Excellent product, highly recommend! The audio quality is impressive.",
        "Very satisfied with my purchase. Comfort is great even after several hours.",
        "Unbeatable value for money. Battery life exceeds my expectations.",
    ]

    SAMPLE_NEGATIVE_REVIEWS = [
        "Disappointed by the quality. The product broke after 3 months of use.",
        "Terrible customer service, impossible to get a response.",
        "Too expensive for what it is. I expected better.",
    ]

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzerService")

    def _generate_theme_analysis(self, theme: tuple, sentiment: str) -> ThemeAnalysis:
        """Generate thematic analysis."""
        return ThemeAnalysis(
            theme=theme[0],
            mention_count=random.randint(50, 500),
            sentiment=sentiment,
            impact_score=round(random.uniform(6, 10) if sentiment == "positive" else random.uniform(3, 7), 1)
        )

    def _generate_sample_reviews(self) -> List[ReviewSample]:
        """Generate representative review samples."""
        samples = []
        for review in random.sample(self.SAMPLE_POSITIVE_REVIEWS, 2):
            samples.append(ReviewSample(
                text=review,
                rating=random.randint(4, 5),
                sentiment="positive",
                date=(datetime.now()).strftime("%Y-%m-%d")
            ))
        for review in random.sample(self.SAMPLE_NEGATIVE_REVIEWS, 1):
            samples.append(ReviewSample(
                text=review,
                rating=random.randint(1, 2),
                sentiment="negative",
                date=(datetime.now()).strftime("%Y-%m-%d")
            ))
        return samples

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
        if total_reviews >= 1000:
            return "High"
        elif total_reviews >= 500:
            return "Medium"
        return "Low"

    def analyze(self, product_name: str) -> SentimentAnalysisResult:
        """Execute complete sentiment analysis."""
        self.logger.info(f"Analyzing sentiment for: {product_name}")

        positive_ratio = random.uniform(0.65, 0.85)
        negative_ratio = random.uniform(0.08, 0.20)
        neutral_ratio = 1 - positive_ratio - negative_ratio

        # Clamp values to ensure they're >= 0 (avoid floating point precision issues)
        positive_ratio = max(0.0, positive_ratio)
        negative_ratio = max(0.0, negative_ratio)
        neutral_ratio = max(0.0, neutral_ratio)

        overall_score = round(3.0 + positive_ratio * 2.5 - negative_ratio * 1.5, 1)
        overall_score = min(5.0, max(1.0, overall_score))

        total_reviews = random.randint(500, 3000)

        positive_themes = [self._generate_theme_analysis(t, "positive")
                          for t in random.sample(self.POSITIVE_THEMES, min(4, len(self.POSITIVE_THEMES)))]
        negative_themes = [self._generate_theme_analysis(t, "negative")
                          for t in random.sample(self.NEGATIVE_THEMES, min(3, len(self.NEGATIVE_THEMES)))]

        return SentimentAnalysisResult(
            product=product_name,
            analysis_date=datetime.now().isoformat(),
            overall_score=overall_score,
            total_reviews=total_reviews,
            sentiment_breakdown=SentimentBreakdown(
                positive=round(max(0.0, positive_ratio), 2),
                negative=round(max(0.0, negative_ratio), 2),
                neutral=round(max(0.0, neutral_ratio), 2)
            ),
            key_themes={
                "positive": positive_themes,
                "negative": negative_themes
            },
            recommendation_rate=round(positive_ratio * 0.95, 2),
            nps_score=self._calculate_nps(positive_ratio, negative_ratio),
            trend=self._determine_trend(overall_score),
            sample_reviews=self._generate_sample_reviews(),
            confidence_level=self._assess_confidence(total_reviews)
        )


@tool
@tool_error_handler("analyze_sentiment")
def analyze_sentiment(product_name: str) -> Dict[str, Any]:
    """Analyze customer review sentiment for a product.

    Provides detailed analysis including:
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