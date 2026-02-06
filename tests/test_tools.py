import pytest
import json
from src.tools.product_scraper import scrape_product_data, ProductScraperService
from src.tools.competitor_analyzer import analyze_competitors, CompetitorAnalyzerService
from src.tools.sentiment_analyzer import analyze_sentiment, SentimentAnalyzerService
from src.tools.report_generator import generate_report, ReportGeneratorService
from src.tools.base import ToolError, tool_error_handler


class TestProductScraper:
    """Tests pour le scraper de produits."""

    def test_scrape_product_data_returns_valid_structure(self, sample_product_name):
        result = scrape_product_data.invoke(sample_product_name)

        assert "name" in result
        assert "average_price" in result
        assert "price_range" in result
        assert "top_sellers" in result
        assert result["name"] == sample_product_name

    def test_scrape_product_data_price_range_valid(self, sample_product_name):
        result = scrape_product_data.invoke(sample_product_name)

        assert result["price_range"]["min"] <= result["average_price"]
        assert result["price_range"]["max"] >= result["average_price"]

    def test_scraper_service_detects_category(self):
        service = ProductScraperService()

        assert "Audio" in service._detect_category("écouteurs bluetooth")
        assert "Mobile" in service._detect_category("téléphone samsung")
        assert "General" in service._detect_category("produit inconnu")

    def test_scrape_product_data_has_sellers(self, sample_product_name):
        result = scrape_product_data.invoke(sample_product_name)

        assert len(result["top_sellers"]) > 0
        assert all("price" in s for s in result["top_sellers"])


class TestCompetitorAnalyzer:
    """Tests pour l'analyseur de concurrence."""

    def test_analyze_competitors_returns_valid_structure(self, sample_category):
        result = analyze_competitors.invoke(sample_category)

        assert "competitors" in result
        assert "market_concentration" in result
        assert "opportunities" in result
        assert "threats" in result

    def test_analyze_competitors_has_competitors(self, sample_category):
        result = analyze_competitors.invoke(sample_category)

        assert len(result["competitors"]) > 0
        for comp in result["competitors"]:
            assert "name" in comp
            assert "market_share" in comp
            assert 0 <= comp["market_share"] <= 100

    def test_competitor_service_market_concentration(self):
        service = CompetitorAnalyzerService()
        result = service.analyze("Electronics/Audio")

        assert result.market_concentration in [
            "Fortement concentré", "Modérément concentré", "Fragmenté"
        ]


class TestSentimentAnalyzer:
    """Tests pour l'analyseur de sentiment."""

    def test_analyze_sentiment_returns_valid_structure(self, sample_product_name):
        result = analyze_sentiment.invoke(sample_product_name)

        assert "overall_score" in result
        assert "sentiment_breakdown" in result
        assert "recommendation_rate" in result
        assert "nps_score" in result

    def test_analyze_sentiment_score_in_range(self, sample_product_name):
        result = analyze_sentiment.invoke(sample_product_name)

        assert 1.0 <= result["overall_score"] <= 5.0
        assert 0 <= result["recommendation_rate"] <= 1
        assert -100 <= result["nps_score"] <= 100

    def test_sentiment_breakdown_sums_to_one(self, sample_product_name):
        result = analyze_sentiment.invoke(sample_product_name)
        breakdown = result["sentiment_breakdown"]

        total = breakdown["positive"] + breakdown["negative"] + breakdown["neutral"]
        assert 0.99 <= total <= 1.01  # Allow floating point tolerance


class TestReportGenerator:
    """Tests pour le générateur de rapports."""

    def test_generate_report_returns_markdown(
        self, sample_product_data, sample_competitor_data, sample_sentiment_data
    ):
        result = generate_report.invoke({
            "product_data": json.dumps(sample_product_data),
            "competitor_data": json.dumps(sample_competitor_data),
            "sentiment_data": json.dumps(sample_sentiment_data)
        })

        assert "# " in result  # Markdown headers
        assert "Rapport" in result
        assert "Recommandations" in result

    def test_generate_report_contains_product_info(
        self, sample_product_data, sample_competitor_data, sample_sentiment_data
    ):
        result = generate_report.invoke({
            "product_data": json.dumps(sample_product_data),
            "competitor_data": json.dumps(sample_competitor_data),
            "sentiment_data": json.dumps(sample_sentiment_data)
        })

        assert sample_product_data["name"] in result

    def test_report_service_handles_empty_data(self):
        service = ReportGeneratorService()
        result = service.generate("{}", "{}", "{}")

        assert "Rapport" in result
        assert "non disponibles" in result or "N/A" in result


class TestToolErrorHandling:
    """Tests pour la gestion des erreurs."""

    def test_tool_error_contains_tool_name(self):
        error = ToolError("test_tool", "Test error message")

        assert "test_tool" in str(error)
        assert "Test error message" in str(error)

    def test_tool_error_handler_decorator(self):
        @tool_error_handler("test_decorated")
        def failing_function():
            raise ValueError("Original error")

        with pytest.raises(ToolError) as exc_info:
            failing_function()

        assert "test_decorated" in str(exc_info.value)

    def test_tool_error_handler_success(self):
        @tool_error_handler("test_success")
        def successful_function():
            return {"status": "ok"}

        result = successful_function()
        assert result["status"] == "ok"