"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class MergeType(str, Enum):
    """Types of merge operations"""
    FULL_OUTER = "full_outer"
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"


class ColumnMapping(BaseModel):
    """Column mapping between datasets"""
    dataset_a_col: str
    dataset_b_col: str
    unified_name: str
    confidence: int = Field(ge=0, le=100)
    reasoning: str
    requires_transformation: bool = False
    transformation: Optional[str] = None


class Conflict(BaseModel):
    """Detected mapping conflict"""
    dataset_a_col: Optional[str] = None
    dataset_b_col: Optional[str] = None
    issue: str
    confidence: int = Field(ge=0, le=100)
    requires_human_review: bool = True
    jira_ticket: Optional[str] = None


class DatasetInfo(BaseModel):
    """Information about an uploaded dataset"""
    filename: str
    size_bytes: int
    snowflake_table: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None


class UploadResponse(BaseModel):
    """Response for file upload"""
    session_id: str
    status: str
    dataset1: DatasetInfo
    dataset2: DatasetInfo


class AnalyzeRequest(BaseModel):
    """Request for schema analysis"""
    session_id: str


class SchemaAnalysis(BaseModel):
    """Schema analysis results"""
    table_name: str
    columns: List[Dict[str, Any]]
    row_count: int
    sample_data: List[Dict[str, Any]]
    semantic_understanding: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response for schema analysis"""
    status: str  # "ready_to_merge" or "requires_approval"
    mappings: List[ColumnMapping]
    conflicts: List[Conflict]
    schema_analysis: Dict[str, SchemaAnalysis]
    processing_time_seconds: float


class ConflictResolution(BaseModel):
    """Resolution for a conflict"""
    resolution: str
    notes: Optional[str] = None


class ApproveRequest(BaseModel):
    """Request to approve mappings and start merge"""
    session_id: str
    approved_mappings: List[ColumnMapping]
    merge_type: MergeType = MergeType.FULL_OUTER
    conflict_resolutions: Optional[Dict[str, ConflictResolution]] = None


class ApproveResponse(BaseModel):
    """Response for approval"""
    job_id: str
    status: str
    estimated_duration_seconds: float
    agents_spawned: Dict[str, int]
    snowflake_warehouse: str


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    progress_percentage: int
    current_step: Optional[str] = None
    agents_active: int
    elapsed_time_seconds: Optional[float] = None
    logs: List[Dict[str, str]]
    errors: List[Dict[str, str]]


class QualityCheck(BaseModel):
    """Quality check result"""
    status: str  # "passed", "warning", or "failed"
    details: Dict[str, Any]


class ValidateResponse(BaseModel):
    """Validation response"""
    overall_status: str
    checks: Dict[str, QualityCheck]
    recommendations: List[str]
    jira_tickets: List[str]


class ChatRequest(BaseModel):
    """Chat request to Master Agent"""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response from Master Agent"""
    answer: str
    reasoning: Optional[str] = None
    confidence: int
    suggested_action: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    agents: Dict[str, Any]

