from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AnalysisType(str, Enum):
    FULL = "full"
    PRODUCT_ONLY = "product_only"
    COMPETITOR_ONLY = "competitor_only"
    SENTIMENT_ONLY = "sentiment_only"


class AnalysisRequest(BaseModel):
    """Requête d'analyse de marché."""
    product_name: str = Field(..., min_length=1, description="Nom du produit à analyser")
    analysis_type: AnalysisType = Field(default=AnalysisType.FULL, description="Type d'analyse")
    include_recommendations: bool = Field(default=True, description="Inclure les recommandations")


class AnalysisResponse(BaseModel):
    """Réponse d'analyse de marché."""
    success: bool
    product_name: str
    report: str
    steps_executed: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Réponse de santé de l'API."""
    status: str
    version: str