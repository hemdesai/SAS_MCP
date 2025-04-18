from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field
from enum import Enum

# --- Core Error Model ---

class MCPError(BaseModel):
    error: Optional[str] = Field(None, description="MCP error code (mapped from Viya errorCode)")
    message: Optional[str] = Field(None, description="Human-readable error message")
    details: Optional[List[Any]] = Field(None, description="Additional error details from Viya, if any")

# --- /run Endpoint ---

class RunRequest(BaseModel):
    code: str = Field(..., description="SAS code to execute")
    session_id: Optional[str] = Field(None, description="Existing Viya session ID (if reusing session)")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional execution options")

class RunResponse(BaseModel):
    job_id: Optional[str] = Field(None, description="Unique job identifier")
    session_id: Optional[str] = Field(None, description="Viya session ID")
    state: str = Field(..., description="Job state (e.g., 'completed', 'running', 'failed')")
    condition_code: Optional[int] = Field(None, description="Viya conditionCode or -1 on error")
    log: Optional[str] = Field(None, description="SAS log output")
    listing: Optional[str] = Field(None, description="SAS listing output")
    data: Optional[Any] = Field(None, description="Result data (tables, etc.)")
    message: Optional[str] = Field(None, description="Human-readable message (success or error)")
    error: Optional[str] = Field(None, description="Error code if failed")

# --- /status Endpoint ---

class StatusRequest(BaseModel):
    job_id: str = Field(..., description="Job identifier to query")
    session_id: Optional[str] = Field(None, description="Session ID (optional)")

class StatusResponse(BaseModel):
    job_id: Optional[str] = Field(None, description="Job identifier")
    session_id: Optional[str] = Field(None, description="Session ID")
    state: str = Field(..., description="Current job/session state")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error code if failed")

# --- /results Endpoint ---

class ResultsRequest(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    session_id: Optional[str] = Field(None, description="Session ID (optional)")

class ResultsResponse(BaseModel):
    job_id: Optional[str] = Field(None, description="Job identifier")
    session_id: Optional[str] = Field(None, description="Session ID")
    log: Optional[str] = Field(None, description="SAS log output")
    listing: Optional[str] = Field(None, description="SAS listing output")
    data: Optional[Any] = Field(None, description="Result data (tables, etc.)")
    answer: Optional[str] = Field(None, description="Extracted value from log, if any")
    message: Optional[str] = Field(None, description="Message or status")
    error: Optional[str] = Field(None, description="Error code if failed")

class CancelRequest(BaseModel):
    job_id: str = Field(..., description="Job identifier to cancel")
    session_id: Optional[str] = Field(None, description="Session ID (optional)")

class CancelResponse(BaseModel):
    job_id: Optional[str] = Field(None, description="Job identifier")
    session_id: Optional[str] = Field(None, description="Session ID")
    state: str = Field(..., description="Cancel state (e.g., 'cancelled', 'not_found', 'error')")
    message: Optional[str] = Field(None, description="Message or status")
    error: Optional[str] = Field(None, description="Error code if failed")

# --- /health Endpoint ---

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status ('ok', 'degraded', 'error')")
    version: Optional[str] = Field(None, description="API version")
    message: Optional[str] = Field(None, description="Additional info or diagnostics")

# --- Unified Error Response (for FastAPI exception handlers) ---

class ErrorResponse(BaseModel):
    state: str = Field("failed", description="Always 'failed' for error responses")
    condition_code: int = Field(-1, description="Always -1 for error responses")
    message: str = Field(..., description="Human-readable error message")
    error: Optional[str] = Field(None, description="Error code")
    details: Optional[List[Any]] = Field(None, description="Additional details")