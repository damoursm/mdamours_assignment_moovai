from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AnalysisType(str, Enum):
    FULL = "full"
    PRODUCT_ONLY = "product_only"
    COMPETITOR_ONLY = "competitor_only"
    SENTIMENT_ONLY = "sentiment_only"


class AnalysisRequest(BaseModel):
    """Market analysis request."""
    product_name: str = Field(..., min_length=1, description="Product name to analyze")
    analysis_type: AnalysisType = Field(default=AnalysisType.FULL, description="Analysis type")
    include_recommendations: bool = Field(default=True, description="Include recommendations")


class AnalysisResponse(BaseModel):
    """Market analysis response."""
    success: bool
    product_name: str
    report: str
    steps_executed: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """API health response."""
    status: str
    version: str