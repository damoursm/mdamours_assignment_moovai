from fastapi import APIRouter, HTTPException
from src.api.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from src.agent import MarketAnalysisGraph
from typing import Any

router = APIRouter()


def extract_text_from_response(response: Any) -> str:
    """Extract text content from LLM response."""
    if isinstance(response, str):
        return response

    # Handle AIMessage or similar objects with content attribute
    content = getattr(response, 'content', response)

    if isinstance(content, str):
        return content

    # Handle list of content blocks (e.g., [{'type': 'text', 'text': '...'}])
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return ''.join(text_parts)

    return str(content)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_market(request: AnalysisRequest):
    try:
        graph = MarketAnalysisGraph()
        result = graph.run(request.product_name)

        # Extract text from report in case it's a content block list
        report = extract_text_from_response(result.get("report", ""))

        return AnalysisResponse(
            success=True,
            product_name=result["product_name"],
            report=report,
            steps_executed=result["steps_executed"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """Liste les outils disponibles pour l'agent."""
    return {
        "tools": [
            {"name": "scrape_product_data", "description": "Collecte les données produit"},
            {"name": "analyze_competitors", "description": "Analyse la concurrence"},
            {"name": "analyze_sentiment", "description": "Analyse le sentiment client"},
            {"name": "generate_report", "description": "Génère le rapport final"}
        ]
    }