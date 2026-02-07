from typing import Dict, Any, Optional
from langchain.tools import tool
from pydantic import BaseModel
import logging
from datetime import datetime
import json

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class ReportSection(BaseModel):
    """Report section."""
    title: str
    content: str
    priority: int


class ReportGeneratorService:
    """Strategic report generation service."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ReportGeneratorService")

    def _parse_json_safely(self, data: str) -> Dict:
        """Parse JSON safely."""
        if isinstance(data, dict):
            return data
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            self.logger.warning(f"Failed to parse JSON: {data[:100]}...")
            return {}

    def _generate_executive_summary(self, product: Dict, sentiment: Dict) -> str:
        """Generate executive summary."""
        product_name = product.get('name', 'Analyzed Product')
        description = product.get('description', 'A consumer product available across major North American e-commerce platforms.')
        score = sentiment.get('overall_score', 'N/A')
        recommendation = sentiment.get('recommendation_rate', 0) * 100

        return f"""
### Executive Summary

**{product_name}** presents a favorable market positioning with a customer satisfaction score of **{score}/5** and a recommendation rate of **{recommendation:.0f}%**.

**Product Description:** {description}

The analysis reveals significant opportunities for price positioning optimization and customer experience improvement.
"""

    def _generate_product_section(self, product: Dict) -> str:
        """Generate product section."""
        if not product:
            return "### Product Data\n*Data not available*\n"

        price_range = product.get('price_range', {})
        sellers = product.get('top_sellers', [])

        sellers_text = ""
        for s in sellers[:3]:
            sellers_text += f"  - {s.get('name', 'N/A')}: ${s.get('price', 'N/A')}\n"

        return f"""
### 1. Product Analysis

| Metric | Value |
|--------|-------|
| **Product** | {product.get('name', 'N/A')} |
| **Average Price** | ${product.get('average_price', 'N/A')} |
| **Price Range** | ${price_range.get('min', 'N/A')} - ${price_range.get('max', 'N/A')} |
| **Availability** | {product.get('availability', 'N/A')} |
| **Number of Sellers** | {product.get('sellers_count', 'N/A')} |
| **Category** | {product.get('category', 'N/A')} |

**Top Sellers:**
{sellers_text}
"""

    def _generate_competitor_section(self, competitors: Dict) -> str:
        """Generate competitive section."""
        if not competitors:
            return "### 2. Competitive Analysis\n*Data not available*\n"

        comp_list = competitors.get('competitors', [])
        concentration = competitors.get('market_concentration', 'N/A')

        comp_table = "| Competitor | Market Share | Strategy | Segment |\n"
        comp_table += "|------------|--------------|----------|----------|\n"
        for c in comp_list[:5]:
            comp_table += f"| {c.get('name', 'N/A')} | {c.get('market_share', 0):.1f}% | {c.get('price_strategy', 'N/A')} | {c.get('target_segment', 'N/A')} |\n"

        opportunities = competitors.get('opportunities', [])
        opp_text = "\n".join([f"- {o}" for o in opportunities])

        threats = competitors.get('threats', [])
        threat_text = "\n".join([f"- {t}" for t in threats])

        return f"""
### 2. Competitive Analysis

**Market Concentration:** {concentration}

{comp_table}

**Identified Opportunities:**
{opp_text}

**Threats:**
{threat_text}
"""

    def _generate_sentiment_section(self, sentiment: Dict) -> str:
        """Generate sentiment section."""
        if not sentiment:
            return "### 3. Customer Sentiment Analysis\n*Data not available*\n"

        breakdown = sentiment.get('sentiment_breakdown', {})
        themes = sentiment.get('key_themes', {})

        positive_themes = themes.get('positive', [])
        pos_text = "\n".join([f"- **{t.get('theme', 'N/A')}** (impact: {t.get('impact_score', 0)}/10, mentions: {t.get('mention_count', 0)})"
                              for t in positive_themes[:4]])

        negative_themes = themes.get('negative', [])
        neg_text = "\n".join([f"- **{t.get('theme', 'N/A')}** (impact: {t.get('impact_score', 0)}/10, mentions: {t.get('mention_count', 0)})"
                              for t in negative_themes[:3]])

        return f"""
### 3. Customer Sentiment Analysis

| Indicator | Value |
|-----------|-------|
| **Overall Score** | {sentiment.get('overall_score', 'N/A')}/5 |
| **Number of Reviews** | {sentiment.get('total_reviews', 'N/A')} |
| **Recommendation Rate** | {sentiment.get('recommendation_rate', 0) * 100:.0f}% |
| **NPS** | {sentiment.get('nps_score', 'N/A')} |
| **Trend** | {sentiment.get('trend', 'N/A')} |
| **Confidence** | {sentiment.get('confidence_level', 'N/A')} |

**Sentiment Distribution:**
- Positive: {breakdown.get('positive', 0) * 100:.0f}%
- Negative: {breakdown.get('negative', 0) * 100:.0f}%
- Neutral: {breakdown.get('neutral', 0) * 100:.0f}%

**Major Positive Themes:**
{pos_text}

**Areas for Improvement:**
{neg_text}
"""

    def _generate_recommendations(self, product: Dict, competitors: Dict, sentiment: Dict) -> str:
        """Generate strategic recommendations."""
        recommendations = []

        # Price recommendation
        if product:
            price_range = product.get('price_range', {})
            if price_range:
                min_price = price_range.get('min', 0)
                recommendations.append(
                    f"**Pricing Strategy:** Position price around ${min_price * 1.1:.2f} to be competitive while preserving margins"
                )

        # Competition recommendation
        if competitors:
            opportunities = competitors.get('opportunities', [])
            if opportunities:
                recommendations.append(f"**Market Opportunity:** {opportunities[0]}")

        # Sentiment recommendation
        if sentiment:
            negative_themes = sentiment.get('key_themes', {}).get('negative', [])
            if negative_themes:
                top_issue = negative_themes[0].get('theme', 'weaknesses')
                recommendations.append(f"**Priority Improvement:** Address the {top_issue} issue identified in reviews")

            positive_themes = sentiment.get('key_themes', {}).get('positive', [])
            if positive_themes:
                strength = positive_themes[0].get('theme', 'strengths')
                recommendations.append(f"**Competitive Advantage:** Capitalize on {strength} in marketing communications")

        recommendations.append("**Distribution:** Strengthen presence on high-traffic platforms (Amazon, Walmart, Target, Best Buy)")
        recommendations.append("**Retention:** Implement post-purchase follow-up program to improve NPS")

        rec_text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(recommendations[:6])])

        return f"""
### 4. Strategic Recommendations

{rec_text}
"""

    def _generate_action_plan(self) -> str:
        """Generate action plan."""
        return """
### 5. Action Plan

| Priority | Action | Timeline | Expected Impact |
|----------|--------|----------|-----------------|
| 🔴 High | Pricing strategy adjustment | 2 weeks | +15% conversions |
| 🟠 Medium | Customer service improvement | 1 month | +10 pts NPS |
| 🟢 Normal | Product listing optimization | 3 weeks | +8% traffic |
| 🟢 Normal | Loyalty program | 2 months | +20% retention |

---
*Report automatically generated by Market Analysis Agent*
"""

    def generate(self, product_data: str, competitor_data: str, sentiment_data: str) -> str:
        """Generate complete report."""
        self.logger.info("Generating comprehensive market analysis report")

        product = self._parse_json_safely(product_data)
        competitors = self._parse_json_safely(competitor_data)
        sentiment = self._parse_json_safely(sentiment_data)

        report = f"""
# 📊 Market Analysis Report

**Generation Date:** {datetime.now().strftime("%m/%d/%Y %H:%M")}

**Market:** North America

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
    """Generate a comprehensive strategic report based on all collected data.

    Compiles analyses into an executive report including:
    - Executive summary with product description
    - Detailed product analysis
    - Competitive analysis with opportunities/threats
    - Customer sentiment analysis
    - Prioritized strategic recommendations
    - Action plan with timelines and impacts

    Args:
        product_data: Product data in JSON (from scrape_product_data)
        competitor_data: Competitive data in JSON (from analyze_competitors)
        sentiment_data: Sentiment data in JSON (from analyze_sentiment)

    Returns:
        Complete strategic report formatted in Markdown
    """
    service = ReportGeneratorService()
    return service.generate(product_data, competitor_data, sentiment_data)