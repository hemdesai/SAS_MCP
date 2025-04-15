from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse, ErrorResponse
)
from mcp_sasviya import sas_client
import logging, traceback

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="MCP SAS Viya API",
    description="Unified API for submitting, managing, and retrieving SAS Viya jobs.",
    version="1.0.0"
)

@app.post("/run", response_model=RunResponse, responses={400: {"model": ErrorResponse}})
def run_endpoint(request: RunRequest):
    response = sas_client.run_code(request)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@app.get("/status", response_model=StatusResponse, responses={400: {"model": ErrorResponse}})
def status_endpoint(
    job_id: str = Query(..., description="Job identifier"),
    session_id: str = Query(None, description="Session ID (optional)")
):
    response = sas_client.get_status(job_id, session_id)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@app.get("/results", response_model=ResultsResponse, responses={400: {"model": ErrorResponse}})
def results_endpoint(
    job_id: str = Query(..., description="Job identifier"),
    session_id: str = Query(None, description="Session ID (optional)")
):
    response = sas_client.get_results(job_id, session_id)
    if response.error:
        raise HTTPException(status_code=400, detail=response.message)
    return response

@app.post("/cancel", response_model=CancelResponse, responses={400: {"model": ErrorResponse}})
def cancel_endpoint(request: CancelRequest):
    response = sas_client.cancel_job(request)
    if response.state == "failed":
        raise HTTPException(status_code=400, detail=response.message)
    return response

@app.get("/health", response_model=HealthResponse)
def health_endpoint():
    return sas_client.check_health()