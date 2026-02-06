from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import random

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class CompetitorProfile(BaseModel):
    """Profil détaillé d'un concurrent."""
    name: str
    market_share: float = Field(ge=0, le=100)
    price_strategy: str
    price_index: float
    strengths: List[str]
    weaknesses: List[str]
    target_segment: str
    online_presence_score: float = Field(ge=0, le=10)


class CompetitorAnalysisResult(BaseModel):
    """Résultat complet de l'analyse concurrentielle."""
    category: str
    analysis_date: str
    competitors: List[CompetitorProfile]
    market_concentration: str
    total_market_share_analyzed: float
    opportunities: List[str]
    threats: List[str]


class CompetitorAnalyzerService:
    """Service d'analyse concurrentielle."""

    COMPETITOR_DATABASE = {
        "Electronics/Audio": [
            {"name": "Sony", "base_share": 22.0, "strategy": "Premium", "segment": "Haut de gamme"},
            {"name": "JBL", "base_share": 18.5, "strategy": "Mid-range", "segment": "Grand public"},
            {"name": "Bose", "base_share": 15.0, "strategy": "Premium", "segment": "Audiophiles"},
            {"name": "Sennheiser", "base_share": 12.0, "strategy": "Premium", "segment": "Professionnels"},
            {"name": "Anker", "base_share": 8.5, "strategy": "Budget", "segment": "Prix bas"},
        ],
        "Electronics/Mobile": [
            {"name": "Apple", "base_share": 28.0, "strategy": "Premium", "segment": "Écosystème"},
            {"name": "Samsung", "base_share": 25.0, "strategy": "Multi-segment", "segment": "Tous publics"},
            {"name": "Xiaomi", "base_share": 15.0, "strategy": "Budget", "segment": "Prix agressif"},
        ],
        "default": [
            {"name": "Leader Marché", "base_share": 25.0, "strategy": "Premium", "segment": "Haut de gamme"},
            {"name": "Challenger", "base_share": 18.0, "strategy": "Mid-range", "segment": "Grand public"},
            {"name": "Disrupteur", "base_share": 12.0, "strategy": "Budget", "segment": "Prix bas"},
        ]
    }

    STRENGTH_POOL = [
        "Forte notoriété de marque", "Réseau de distribution étendu", "Innovation produit",
        "Service après-vente réputé", "Prix compétitifs", "Large gamme de produits",
        "Qualité perçue élevée", "Présence marketing forte", "Fidélité client"
    ]
    WEAKNESS_POOL = [
        "Prix élevés", "Gamme limitée", "Faible présence en ligne", "SAV critiqué",
        "Innovation lente", "Image de marque vieillissante", "Distribution limitée"
    ]

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CompetitorAnalyzerService")

    def _get_competitors_for_category(self, category: str) -> List[Dict]:
        """Récupère les concurrents pour une catégorie."""
        for cat_key, competitors in self.COMPETITOR_DATABASE.items():
            if cat_key.lower() in category.lower() or category.lower() in cat_key.lower():
                return competitors
        return self.COMPETITOR_DATABASE["default"]

    def _generate_competitor_profile(self, base_data: Dict) -> CompetitorProfile:
        """Génère un profil détaillé de concurrent."""
        variation = random.uniform(-3, 3)
        market_share = max(1, base_data["base_share"] + variation)

        price_indices = {"Premium": 1.3, "Mid-range": 1.0, "Budget": 0.7, "Multi-segment": 1.1}
        price_index = price_indices.get(base_data["strategy"], 1.0)

        return CompetitorProfile(
            name=base_data["name"],
            market_share=round(market_share, 1),
            price_strategy=base_data["strategy"],
            price_index=round(price_index + random.uniform(-0.1, 0.1), 2),
            strengths=random.sample(self.STRENGTH_POOL, k=random.randint(2, 4)),
            weaknesses=random.sample(self.WEAKNESS_POOL, k=random.randint(1, 3)),
            target_segment=base_data["segment"],
            online_presence_score=round(random.uniform(6, 10), 1)
        )

    def _assess_market_concentration(self, competitors: List[CompetitorProfile]) -> str:
        """Évalue la concentration du marché."""
        top3_share = sum(sorted([c.market_share for c in competitors], reverse=True)[:3])
        if top3_share > 70:
            return "Fortement concentré"
        elif top3_share > 50:
            return "Modérément concentré"
        return "Fragmenté"

    def _identify_opportunities(self, competitors: List[CompetitorProfile]) -> List[str]:
        """Identifie les opportunités de marché."""
        opportunities = []
        avg_price_index = sum(c.price_index for c in competitors) / len(competitors)

        if avg_price_index > 1.1:
            opportunities.append("Opportunité de positionnement prix agressif")
        if not any("Budget" in c.price_strategy for c in competitors):
            opportunities.append("Segment entrée de gamme sous-exploité")
        if any(c.online_presence_score < 7 for c in competitors):
            opportunities.append("Potentiel de différenciation par le digital")
        opportunities.append("Différenciation par le service client")

        return opportunities[:4]

    def _identify_threats(self, competitors: List[CompetitorProfile]) -> List[str]:
        """Identifie les menaces du marché."""
        threats = ["Guerre des prix potentielle", "Nouveaux entrants disruptifs"]
        if any(c.market_share > 25 for c in competitors):
            threats.append("Position dominante d'un acteur majeur")
        return threats

    def analyze(self, category: str) -> CompetitorAnalysisResult:
        """Exécute l'analyse concurrentielle complète."""
        self.logger.info(f"Analyzing competitors for category: {category}")

        base_competitors = self._get_competitors_for_category(category)
        competitors = [self._generate_competitor_profile(c) for c in base_competitors]

        return CompetitorAnalysisResult(
            category=category,
            analysis_date=datetime.now().isoformat(),
            competitors=competitors,
            market_concentration=self._assess_market_concentration(competitors),
            total_market_share_analyzed=sum(c.market_share for c in competitors),
            opportunities=self._identify_opportunities(competitors),
            threats=self._identify_threats(competitors)
        )


@tool
@tool_error_handler("analyze_competitors")
def analyze_competitors(product_category: str) -> Dict[str, Any]:
    """Analyse les concurrents pour une catégorie de produit donnée.

    Fournit une analyse détaillée incluant:
    - Profils des principaux concurrents avec parts de marché
    - Stratégies de prix et positionnement
    - Forces et faiblesses de chaque concurrent
    - Opportunités et menaces du marché

    Args:
        product_category: La catégorie de produit à analyser (ex: Electronics/Audio)

    Returns:
        Analyse concurrentielle complète avec recommandations
    """
    service = CompetitorAnalyzerService()
    result = service.analyze(product_category)
    return result.model_dump()