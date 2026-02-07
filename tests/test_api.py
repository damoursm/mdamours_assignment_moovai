import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_check_returns_200(self, client):
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_returns_version(self, client):
        response = client.get("/api/v1/health")

        assert "version" in response.json()


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_info(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert "message" in response.json()
        assert "docs" in response.json()


class TestToolsEndpoint:
    """Tests for the tools endpoint."""

    def test_list_tools_returns_tools(self, client):
        response = client.get("/api/v1/tools")

        assert response.status_code == 200
        assert "tools" in response.json()
        assert len(response.json()["tools"]) == 4


class TestAnalyzeEndpoint:
    """Tests for the analyze endpoint."""

    def test_analyze_requires_product_name(self, client):
        response = client.post("/api/v1/analyze", json={})

        assert response.status_code == 422  # Validation error

    def test_analyze_rejects_empty_product_name(self, client):
        response = client.post("/api/v1/analyze", json={"product_name": ""})

        assert response.status_code == 422

    @patch('src.api.routes.MarketAnalysisGraph')
    def test_analyze_returns_valid_response(self, mock_graph_class, client):
        mock_graph = MagicMock()
        mock_graph.run.return_value = {
            "product_name": "test",
            "report": "Test report",
            "steps_executed": 5
        }
        mock_graph_class.return_value = mock_graph

        response = client.post(
            "/api/v1/analyze",
            json={"product_name": "wireless earbuds"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "report" in response.json()

    @patch('src.api.routes.MarketAnalysisGraph')
    def test_analyze_handles_errors(self, mock_graph_class, client):
        mock_graph_class.side_effect = Exception("Test error")

        response = client.post(
            "/api/v1/analyze",
            json={"product_name": "test product"}
        )

        assert response.status_code == 500


class TestAnalysisRequestValidation:
    """Tests for request validation."""

    def test_valid_full_analysis_type(self, client):
        with patch('src.api.routes.MarketAnalysisGraph') as mock:
            mock.return_value.run.return_value = {
                "product_name": "test",
                "report": "report",
                "steps_executed": 1
            }

            response = client.post(
                "/api/v1/analyze",
                json={"product_name": "test", "analysis_type": "full"}
            )

            assert response.status_code == 200

    def test_invalid_analysis_type(self, client):
        response = client.post(
            "/api/v1/analyze",
            json={"product_name": "test", "analysis_type": "invalid"}
        )

        assert response.status_code == 422