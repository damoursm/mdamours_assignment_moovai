import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from src.agent.graph import MarketAnalysisGraph
from src.agent.state import AgentState


class TestAgentState:
    """Tests for agent state."""

    def test_agent_state_structure(self):
        state: AgentState = {
            "messages": [],
            "product_name": "test product",
            "product_data": None,
            "competitor_data": None,
            "sentiment_data": None,
            "final_report": None,
            "current_step": "init",
            "errors": []
        }

        assert state["product_name"] == "test product"
        assert state["current_step"] == "init"
        assert isinstance(state["errors"], list)


class TestMarketAnalysisGraph:
    """Tests for orchestration graph."""

    @pytest.fixture
    def mock_llm_response(self):
        # Return a proper AIMessage instead of MagicMock
        return AIMessage(content="Test analysis complete")

    @patch('src.agent.graph.ChatGoogleGenerativeAI')
    def test_graph_initialization(self, mock_chat):
        mock_chat.return_value = MagicMock()

        graph = MarketAnalysisGraph()

        assert graph.tools is not None
        assert len(graph.tools) == 4
        assert graph.graph is not None

    @patch('src.agent.graph.ChatGoogleGenerativeAI')
    def test_graph_has_required_tools(self, mock_chat):
        mock_chat.return_value = MagicMock()

        graph = MarketAnalysisGraph()
        tool_names = [t.name for t in graph.tools]

        assert "scrape_product_data" in tool_names
        assert "analyze_competitors" in tool_names
        assert "analyze_sentiment" in tool_names
        assert "generate_report" in tool_names

    @patch('src.agent.graph.ChatGoogleGenerativeAI')
    def test_should_continue_with_tool_calls(self, mock_chat):
        mock_chat.return_value = MagicMock()
        graph = MarketAnalysisGraph()

        # Use AIMessage with tool_calls
        mock_message = AIMessage(content="", tool_calls=[{"name": "test_tool", "id": "1", "args": {}}])

        state = {"messages": [mock_message]}
        result = graph._should_continue(state)

        assert result == "continue"

    @patch('src.agent.graph.ChatGoogleGenerativeAI')
    def test_should_end_without_tool_calls(self, mock_chat):
        mock_chat.return_value = MagicMock()
        graph = MarketAnalysisGraph()

        # Use AIMessage without tool_calls
        mock_message = AIMessage(content="Done")

        state = {"messages": [mock_message]}
        result = graph._should_continue(state)

        assert result == "end"

    @patch('src.agent.graph.ChatGoogleGenerativeAI')
    def test_run_returns_expected_structure(self, mock_chat):
        mock_llm_response = AIMessage(content="Test analysis complete")

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_llm.bind_tools.return_value = mock_llm
        mock_chat.return_value = mock_llm

        graph = MarketAnalysisGraph()
        result = graph.run("test product")

        assert "product_name" in result
        assert "report" in result
        assert "steps_executed" in result
        assert result["product_name"] == "test product"