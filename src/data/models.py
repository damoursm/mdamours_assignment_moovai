from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRecord(BaseModel):
    """Storage for analysis results."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    analysis_type: str
    status: AnalysisStatus
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Results
    product_data: Optional[Dict[str, Any]] = None
    competitor_data: Optional[Dict[str, Any]] = None
    sentiment_data: Optional[Dict[str, Any]] = None
    final_report: Optional[str] = None

    # Metadata
    execution_time_ms: Optional[float] = None
    steps_executed: int = 0
    errors: List[str] = []


class RequestHistory(BaseModel):
    """User request history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    product_name: str
    analysis_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    analysis_id: Optional[str] = None
    response_time_ms: Optional[float] = None


class CachedData(BaseModel):
    """Cache for collected data."""
    key: str  # Format: "{tool_name}:{input_hash}"
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    hit_count: int = 0
    source_tool: str


class AgentConfiguration(BaseModel):
    """Agent configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 4096
    tools_enabled: List[str] = []
    system_prompt: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)