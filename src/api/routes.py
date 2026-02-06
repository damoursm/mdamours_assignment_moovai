from fastapi import APIRouter, HTTPException
from src.api.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from src.agent import MarketAnalysisGraph

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_market(request: AnalysisRequest):
    try:
        graph = MarketAnalysisGraph()
        result = graph.run(request.product_name)
        return AnalysisResponse(
            success=True,
            product_name=result["product_name"],
            report=result["report"],
            steps_executed=result["steps_executed"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))