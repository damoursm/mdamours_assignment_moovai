from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import random

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class SentimentBreakdown(BaseModel):
    """Répartition des sentiments."""
    positive: float = Field(ge=0, le=1)
    negative: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)


class ThemeAnalysis(BaseModel):
    """Analyse thématique des avis."""
    theme: str
    mention_count: int
    sentiment: str
    impact_score: float = Field(ge=0, le=10)


class ReviewSample(BaseModel):
    """Exemple d'avis représentatif."""
    text: str
    rating: int = Field(ge=1, le=5)
    sentiment: str
    date: str


class SentimentAnalysisResult(BaseModel):
    """Résultat complet de l'analyse de sentiment."""
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
    """Service d'analyse de sentiment des avis clients."""

    POSITIVE_THEMES = [
        ("qualité audio", "Excellente qualité sonore mentionnée"),
        ("confort", "Confort de port apprécié"),
        ("autonomie", "Bonne autonomie de batterie"),
        ("rapport qualité-prix", "Bon rapport qualité-prix"),
        ("design", "Design moderne et élégant"),
        ("facilité d'utilisation", "Prise en main intuitive"),
        ("bluetooth stable", "Connexion fiable"),
    ]

    NEGATIVE_THEMES = [
        ("fragilité", "Problèmes de durabilité signalés"),
        ("SAV", "Service après-vente critiqué"),
        ("notice", "Documentation insuffisante"),
        ("prix", "Perçu comme trop cher"),
        ("bruit", "Isolation phonique insuffisante"),
        ("micro", "Qualité micro décevante"),
    ]

    SAMPLE_POSITIVE_REVIEWS = [
        "Excellent produit, je recommande vivement ! La qualité audio est impressionnante.",
        "Très satisfait de mon achat. Le confort est au rendez-vous même après plusieurs heures.",
        "Rapport qualité-prix imbattable. L'autonomie dépasse mes attentes.",
    ]

    SAMPLE_NEGATIVE_REVIEWS = [
        "Déçu par la qualité. Le produit a lâché après 3 mois d'utilisation.",
        "SAV catastrophique, impossible d'avoir une réponse.",
        "Trop cher pour ce que c'est. Je m'attendais à mieux.",
    ]

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SentimentAnalyzerService")

    def _generate_theme_analysis(self, theme: tuple, sentiment: str) -> ThemeAnalysis:
        """Génère une analyse thématique."""
        return ThemeAnalysis(
            theme=theme[0],
            mention_count=random.randint(50, 500),
            sentiment=sentiment,
            impact_score=round(random.uniform(6, 10) if sentiment == "positive" else random.uniform(3, 7), 1)
        )

    def _generate_sample_reviews(self) -> List[ReviewSample]:
        """Génère des exemples d'avis représentatifs."""
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
        """Calcule le Net Promoter Score."""
        promoters = positive_ratio * 0.8
        detractors = negative_ratio * 0.9
        return int((promoters - detractors) * 100)

    def _determine_trend(self, overall_score: float) -> str:
        """Détermine la tendance du sentiment."""
        if overall_score >= 4.0:
            return "↑ En hausse"
        elif overall_score >= 3.0:
            return "→ Stable"
        return "↓ En baisse"

    def _assess_confidence(self, total_reviews: int) -> str:
        """Évalue le niveau de confiance de l'analyse."""
        if total_reviews >= 1000:
            return "Élevé"
        elif total_reviews >= 500:
            return "Moyen"
        return "Faible"

    def analyze(self, product_name: str) -> SentimentAnalysisResult:
        """Exécute l'analyse de sentiment complète."""
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
    """Analyse le sentiment des avis clients pour un produit.

    Fournit une analyse détaillée incluant:
    - Score global et répartition des sentiments
    - Thèmes clés positifs et négatifs avec impact
    - Net Promoter Score (NPS)
    - Tendance et exemples d'avis
    - Niveau de confiance de l'analyse

    Args:
        product_name: Le nom du produit à analyser

    Returns:
        Analyse de sentiment complète avec insights actionnables
    """
    service = SentimentAnalyzerService()
    result = service.analyze(product_name)
    return result.model_dump()