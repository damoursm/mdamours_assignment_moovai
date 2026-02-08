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
    """LangGraph graph for market analysis orchestration."""

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
        """Build the agent execution graph."""
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
        """Main agent node that decides actions."""
        system_prompt = """You are an expert e-commerce market analysis agent.

You must analyze the requested product using the available tools in this order:
1. scrape_product_data - to collect product data
2. analyze_competitors - to analyze competition (use the product category)
3. analyze_sentiment - to evaluate customer sentiment
4. generate_report - to create the final report (pass data as JSON)

Execute each tool sequentially and use the results for the final report.
IMPORTANT: You MUST call generate_report as the final step. Do not just summarize the results yourself.
If you have called generate_report, your job is done."""

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = self.llm.invoke(messages)

        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Determine if the agent should continue or stop."""
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"

    def run(self, product_name: str) -> dict:
        """Execute complete analysis for a product."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"Analyze the market for the product: {product_name}")],
            "product_name": product_name,
            "product_data": None,
            "competitor_data": None,
            "sentiment_data": None,
            "final_report": None,
            "current_step": "init",
            "errors": []
        }

        result = self.graph.invoke(initial_state)

        # Extract the final report from the messages
        # We look for the output of the generate_report tool
        final_report = ""
        for message in reversed(result["messages"]):
            if hasattr(message, "tool_calls") and message.tool_calls:
                # This is an AI message calling a tool, check if it called generate_report
                if message.tool_calls[0]['name'] == 'generate_report':
                    # The next message should be the tool output
                    continue
            
            if hasattr(message, "content") and "📊 Market Analysis Report" in str(message.content):
                 final_report = message.content
                 break
            
            # Fallback: if the LLM just printed the report content directly (less likely with tool use but possible)
            if isinstance(message, HumanMessage) is False and "📊 Market Analysis Report" in str(message.content):
                 final_report = message.content
                 break

        # If we still don't have a report, try to find the last tool message which might be the report
        if not final_report:
             for message in reversed(result["messages"]):
                 if hasattr(message, "name") and message.name == "generate_report":
                     final_report = message.content
                     break

        # If still empty, use the last message content as a fallback
        if not final_report and result["messages"]:
            final_report = result["messages"][-1].content

        return {
            "product_name": product_name,
            "report": final_report,
            "steps_executed": len(result["messages"])
        }