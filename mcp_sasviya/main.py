import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, responses, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse, ErrorResponse
)
from mcp_sasviya import sas_client
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="MCP SAS Viya API",
    description="Unified API for submitting, managing, and retrieving SAS Viya jobs.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_build_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')

api_router = APIRouter()

@api_router.get("/status", response_model=StatusResponse, responses={400: {"model": ErrorResponse}})
async def status(job_id: str = Query(..., description="Job identifier"), session_id: Optional[str] = Query(None, description="Session ID (optional)")):
    """
    Check Job Status
    -----------------
    Query the status of a submitted SAS job or session. Returns current state (e.g., running, completed).
    Example use case: Monitor long-running analytics or data processing jobs.
    """
    response = sas_client.get_job_status(job_id, session_id)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@api_router.get("/results", response_model=ResultsResponse, responses={400: {"model": ErrorResponse}})
async def results(job_id: str = Query(..., description="Job identifier"), session_id: Optional[str] = Query(None, description="Session ID (optional)")):
    """
    Fetch Results
    -----------------
    Retrieve logs, output listings, and result data for a completed or failed SAS job.
    Returns logs, data tables, and error details if present, without raising exceptions.
    """
    return sas_client.get_results(job_id, session_id)

@api_router.post("/cancel", response_model=CancelResponse, responses={400: {"model": ErrorResponse}})
async def cancel(request: CancelRequest):
    """
    Cancel a Job
    -----------------
    Stop a SAS job or session that is currently executing.
    Example use case: Abort long-running or stuck jobs to free up compute resources.
    """
    response = sas_client.cancel_job(request)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@api_router.post("/run", response_model=RunResponse, responses={400: {"model": ErrorResponse}})
async def run(request: RunRequest):
    """
    Run SAS Code
    -----------------
    Submit SAS code for execution. Returns a job ID and session ID for tracking.
    Example use case: Automate analytics, reporting, or ETL tasks by submitting code to SAS Viya.
    """
    response = sas_client.run_code(request)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@api_router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health Check
    -----------------
    Confirm that the MCP SAS Viya API server is running and ready to accept requests.
    Used for monitoring and readiness probes in Kubernetes.
    """
    return sas_client.check_health()

@api_router.get("/table")
async def get_table(
    session_id: str = Query(..., description="Session ID"),
    library: str = Query(..., description="Library name (e.g., 'work')"),
    table_name: str = Query(..., description="Table name (e.g., 'work_means')")
):
    """
    Get Table Data
    --------------
    Fetches data from a specified table in a given session and library.
    """
    try:
        table_data = sas_client.get_table(session_id, library, table_name)
        return table_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.include_router(api_router, prefix="/api")

frontend_build_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
from fastapi.staticfiles import StaticFiles

# Serve React build (HTML + static) for all other routes
app.mount(
    "/",
    StaticFiles(directory=frontend_build_dir, html=True),
    name="static",
)
