from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agent.state import AgentState
from src.tools import (
    scrape_product_data,
    analyze_competitors,
    analyze_sentiment,
    generate_report
)
from src.config import get_settings


class MarketAnalysisGraph:
    """Graphe LangGraph pour l'orchestration de l'analyse de marché."""

    def __init__(self):
        settings = get_settings()
        self.tools = [
            scrape_product_data,
            analyze_competitors,
            analyze_sentiment,
            generate_report
        ]
        self.llm = ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.google_api_key,
            temperature=0.1
        ).bind_tools(self.tools)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Construit le graphe d'exécution de l'agent."""
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def _agent_node(self, state: AgentState) -> dict:
        """Noeud principal de l'agent qui décide des actions."""
        system_prompt = """Tu es un agent d'analyse de marché e-commerce expert.

Tu dois analyser le produit demandé en utilisant les outils disponibles dans cet ordre:
1. scrape_product_data - pour collecter les données du produit
2. analyze_competitors - pour analyser la concurrence (utilise la catégorie du produit)
3. analyze_sentiment - pour évaluer le sentiment client
4. generate_report - pour créer le rapport final (passe les données en JSON)

Exécute chaque outil séquentiellement et utilise les résultats pour le rapport final."""

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = self.llm.invoke(messages)

        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Détermine si l'agent doit continuer ou s'arrêter."""
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"

    def run(self, product_name: str) -> dict:
        """Exécute l'analyse complète pour un produit."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"Analyse le marché pour le produit: {product_name}")],
            "product_name": product_name,
            "product_data": None,
            "competitor_data": None,
            "sentiment_data": None,
            "final_report": None,
            "current_step": "init",
            "errors": []
        }

        result = self.graph.invoke(initial_state)

        final_message = result["messages"][-1].content if result["messages"] else ""

        return {
            "product_name": product_name,
            "report": final_message,
            "steps_executed": len(result["messages"])
        }