from typing import Dict, Any, Optional
from langchain.tools import tool
from pydantic import BaseModel
import logging
from datetime import datetime
import json

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class ReportSection(BaseModel):
    """Section du rapport."""
    title: str
    content: str
    priority: int


class ReportGeneratorService:
    """Service de génération de rapports stratégiques."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ReportGeneratorService")

    def _parse_json_safely(self, data: str) -> Dict:
        """Parse JSON de manière sécurisée."""
        if isinstance(data, dict):
            return data
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            self.logger.warning(f"Failed to parse JSON: {data[:100]}...")
            return {}

    def _generate_executive_summary(self, product: Dict, sentiment: Dict) -> str:
        """Génère le résumé exécutif."""
        product_name = product.get('name', 'Produit analysé')
        score = sentiment.get('overall_score', 'N/A')
        recommendation = sentiment.get('recommendation_rate', 0) * 100

        return f"""
### Résumé Exécutif

**{product_name}** présente un positionnement marché favorable avec un score de satisfaction client de **{score}/5** et un taux de recommandation de **{recommendation:.0f}%**.

L'analyse révèle des opportunités significatives d'optimisation du positionnement prix et d'amélioration de l'expérience client.
"""

    def _generate_product_section(self, product: Dict) -> str:
        """Génère la section produit."""
        if not product:
            return "### Données Produit\n*Données non disponibles*\n"

        price_range = product.get('price_range', {})
        sellers = product.get('top_sellers', [])

        sellers_text = ""
        for s in sellers[:3]:
            sellers_text += f"  - {s.get('name', 'N/A')}: {s.get('price', 'N/A')}€\n"

        return f"""
### 1. Analyse Produit

| Métrique | Valeur |
|----------|--------|
| **Produit** | {product.get('name', 'N/A')} |
| **Prix moyen** | {product.get('average_price', 'N/A')}€ |
| **Fourchette de prix** | {price_range.get('min', 'N/A')}€ - {price_range.get('max', 'N/A')}€ |
| **Disponibilité** | {product.get('availability', 'N/A')} |
| **Nombre de vendeurs** | {product.get('sellers_count', 'N/A')} |
| **Catégorie** | {product.get('category', 'N/A')} |

**Top vendeurs:**
{sellers_text}
"""

    def _generate_competitor_section(self, competitors: Dict) -> str:
        """Génère la section concurrentielle."""
        if not competitors:
            return "### 2. Analyse Concurrentielle\n*Données non disponibles*\n"

        comp_list = competitors.get('competitors', [])
        concentration = competitors.get('market_concentration', 'N/A')

        comp_table = "| Concurrent | Part de marché | Stratégie | Segment |\n"
        comp_table += "|------------|----------------|-----------|----------|\n"
        for c in comp_list[:5]:
            comp_table += f"| {c.get('name', 'N/A')} | {c.get('market_share', 0):.1f}% | {c.get('price_strategy', 'N/A')} | {c.get('target_segment', 'N/A')} |\n"

        opportunities = competitors.get('opportunities', [])
        opp_text = "\n".join([f"- {o}" for o in opportunities])

        threats = competitors.get('threats', [])
        threat_text = "\n".join([f"- {t}" for t in threats])

        return f"""
### 2. Analyse Concurrentielle

**Concentration du marché:** {concentration}

{comp_table}

**Opportunités identifiées:**
{opp_text}

**Menaces:**
{threat_text}
"""

    def _generate_sentiment_section(self, sentiment: Dict) -> str:
        """Génère la section sentiment."""
        if not sentiment:
            return "### 3. Analyse du Sentiment Client\n*Données non disponibles*\n"

        breakdown = sentiment.get('sentiment_breakdown', {})
        themes = sentiment.get('key_themes', {})

        positive_themes = themes.get('positive', [])
        pos_text = "\n".join([f"- **{t.get('theme', 'N/A')}** (impact: {t.get('impact_score', 0)}/10, mentions: {t.get('mention_count', 0)})"
                              for t in positive_themes[:4]])

        negative_themes = themes.get('negative', [])
        neg_text = "\n".join([f"- **{t.get('theme', 'N/A')}** (impact: {t.get('impact_score', 0)}/10, mentions: {t.get('mention_count', 0)})"
                              for t in negative_themes[:3]])

        return f"""
### 3. Analyse du Sentiment Client

| Indicateur | Valeur |
|------------|--------|
| **Score global** | {sentiment.get('overall_score', 'N/A')}/5 |
| **Nombre d'avis** | {sentiment.get('total_reviews', 'N/A')} |
| **Taux de recommandation** | {sentiment.get('recommendation_rate', 0) * 100:.0f}% |
| **NPS** | {sentiment.get('nps_score', 'N/A')} |
| **Tendance** | {sentiment.get('trend', 'N/A')} |
| **Confiance** | {sentiment.get('confidence_level', 'N/A')} |

**Répartition des sentiments:**
- Positif: {breakdown.get('positive', 0) * 100:.0f}%
- Négatif: {breakdown.get('negative', 0) * 100:.0f}%
- Neutre: {breakdown.get('neutral', 0) * 100:.0f}%

**Thèmes positifs majeurs:**
{pos_text}

**Points d'amélioration:**
{neg_text}
"""

    def _generate_recommendations(self, product: Dict, competitors: Dict, sentiment: Dict) -> str:
        """Génère les recommandations stratégiques."""
        recommendations = []

        # Recommandation prix
        if product:
            price_range = product.get('price_range', {})
            if price_range:
                min_price = price_range.get('min', 0)
                recommendations.append(
                    f"**Stratégie Prix:** Positionner le prix autour de {min_price * 1.1:.2f}€ pour être compétitif tout en préservant les marges"
                )

        # Recommandation concurrence
        if competitors:
            opportunities = competitors.get('opportunities', [])
            if opportunities:
                recommendations.append(f"**Opportunité Marché:** {opportunities[0]}")

        # Recommandation sentiment
        if sentiment:
            negative_themes = sentiment.get('key_themes', {}).get('negative', [])
            if negative_themes:
                top_issue = negative_themes[0].get('theme', 'points faibles')
                recommendations.append(f"**Amélioration Prioritaire:** Adresser le problème de {top_issue} identifié dans les avis")

            positive_themes = sentiment.get('key_themes', {}).get('positive', [])
            if positive_themes:
                strength = positive_themes[0].get('theme', 'forces')
                recommendations.append(f"**Avantage Concurrentiel:** Capitaliser sur {strength} dans la communication")

        recommendations.append("**Distribution:** Renforcer la présence sur les plateformes à fort trafic")
        recommendations.append("**Fidélisation:** Mettre en place un programme de suivi post-achat pour améliorer le NPS")

        rec_text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(recommendations[:6])])

        return f"""
### 4. Recommandations Stratégiques

{rec_text}
"""

    def _generate_action_plan(self) -> str:
        """Génère le plan d'action."""
        return """
### 5. Plan d'Action

| Priorité | Action | Délai | Impact attendu |
|----------|--------|-------|----------------|
| 🔴 Haute | Ajustement stratégie prix | 2 semaines | +15% conversions |
| 🟠 Moyenne | Amélioration SAV | 1 mois | +10 pts NPS |
| 🟢 Normale | Optimisation fiches produit | 3 semaines | +8% trafic |
| 🟢 Normale | Programme fidélité | 2 mois | +20% rétention |

---
*Rapport généré automatiquement par Market Analysis Agent*
"""

    def generate(self, product_data: str, competitor_data: str, sentiment_data: str) -> str:
        """Génère le rapport complet."""
        self.logger.info("Generating comprehensive market analysis report")

        product = self._parse_json_safely(product_data)
        competitors = self._parse_json_safely(competitor_data)
        sentiment = self._parse_json_safely(sentiment_data)

        report = f"""
# 📊 Rapport d'Analyse de Marché

**Date de génération:** {datetime.now().strftime("%d/%m/%Y %H:%M")}

---

{self._generate_executive_summary(product, sentiment)}

---

{self._generate_product_section(product)}

{self._generate_competitor_section(competitors)}

{self._generate_sentiment_section(sentiment)}

{self._generate_recommendations(product, competitors, sentiment)}

{self._generate_action_plan()}
"""
        return report.strip()


@tool
@tool_error_handler("generate_report")
def generate_report(
    product_data: str,
    competitor_data: str,
    sentiment_data: str
) -> str:
    """Génère un rapport stratégique complet basé sur toutes les données collectées.

    Compile les analyses en un rapport exécutif incluant:
    - Résumé exécutif
    - Analyse produit détaillée
    - Analyse concurrentielle avec opportunités/menaces
    - Analyse du sentiment client
    - Recommandations stratégiques prioritisées
    - Plan d'action avec délais et impacts

    Args:
        product_data: Données produit en JSON (de scrape_product_data)
        competitor_data: Données concurrentielles en JSON (de analyze_competitors)
        sentiment_data: Données de sentiment en JSON (de analyze_sentiment)

    Returns:
        Rapport stratégique complet formaté en Markdown
    """
    service = ReportGeneratorService()
    return service.generate(product_data, competitor_data, sentiment_data)