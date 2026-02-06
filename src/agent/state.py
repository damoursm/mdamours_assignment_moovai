from pydantic import BaseModel, field_validator
from typing import Any, List, Union, TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the market analysis agent."""
    messages: Annotated[list, add_messages]
    product_name: str
    analysis_results: Optional[dict]
    error: Optional[str]


class AnalysisResponse(BaseModel):
    report: str

    @field_validator('report', mode='before')
    @classmethod
    def extract_text_from_content(cls, v: Any) -> str:
        # Handle list of content blocks from LLM
        if isinstance(v, list):
            texts = []
            for item in v:
                if isinstance(item, dict) and 'text' in item:
                    texts.append(item['text'])
                elif isinstance(item, str):
                    texts.append(item)
            return '\n'.join(texts)  # Use newline separator
        return v

    def formatted_report(self) -> str:
        """Return report with proper formatting."""
        return self.report.replace('\\n', '\n')