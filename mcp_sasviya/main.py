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
from mcp_sasviya import mcp_server
from mcp_sasviya import mcp_server

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

from fastapi import Request
from fastapi.responses import JSONResponse

@app.post("/chatbot")
async def chatbot_endpoint(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    session_id = data.get("session_id")
    import re
    tables = []
    # Extract table names from the prompt if present
    if prompt:
        match = re.search(r"Tables:\s*(.*)", prompt, re.IGNORECASE)
        if match:
            table_line = match.group(1)
            tables = [t.strip() for t in table_line.split(",") if t.strip()]
    if not tables:
        tables = ["results"]
    mcp = mcp_server.mcp
    import json
    import logging
    run_req = {"request": {"code": prompt, "session_id": session_id}}
    run_resp = await mcp.call_tool("run", run_req)
    logging.warning(f"run_resp: {run_resp}")
    # Handle if run_resp is a list with TextContent
    job_id = session_id = None
    if isinstance(run_resp, list) and run_resp:
        resp_obj = run_resp[0]
        if hasattr(resp_obj, "text"):
            try:
                run_resp_json = json.loads(resp_obj.text)
                job_id = run_resp_json.get("job_id")
                session_id = run_resp_json.get("session_id")
            except Exception as e:
                logging.error(f"Failed to parse run_resp.text: {e}")
        else:
            job_id = session_id = None
    else:
        job_id = getattr(run_resp, 'job_id', None)
        session_id = getattr(run_resp, 'session_id', None)
    # Poll for job completion
    import time
    status_req = {"job_id": job_id, "session_id": session_id}
    status = await mcp.call_tool("status", status_req)
    import json
    import logging
    for _ in range(30):
        # Handle list/TextContent for status
        status_obj = status
        if isinstance(status, list) and status:
            if hasattr(status[0], "text"):
                try:
                    status_obj = json.loads(status[0].text)
                except Exception as e:
                    logging.error(f"Failed to parse status.text: {e}")
                    status_obj = {}
            else:
                status_obj = {}
        if status_obj.get("state") != "running":
            break
        time.sleep(1)
        status = await mcp.call_tool("status", status_req)
    # After polling, extract final status_obj
    final_status_obj = status
    if isinstance(status, list) and status:
        if hasattr(status[0], "text"):
            try:
                final_status_obj = json.loads(status[0].text)
            except Exception as e:
                logging.error(f"Failed to parse status.text: {e}")
                final_status_obj = {}
        else:
            final_status_obj = {}
    results_req = {"job_id": job_id, "session_id": session_id}
    results = await mcp.call_tool("results", results_req)
    # Handle list/TextContent for results
    results_obj = results
    if isinstance(results, list) and results:
        if hasattr(results[0], "text"):
            try:
                results_obj = json.loads(results[0].text)
            except Exception as e:
                logging.error(f"Failed to parse results.text: {e}")
                results_obj = {}
        else:
            results_obj = {}
    # Fetch all requested tables
    results_tables = {}
    from mcp_sasviya.sas_client import get_table
    for t in tables:
        if session_id and t:
            try:
                results_tables[t] = get_table(session_id, "work", t)
            except Exception as exc:
                results_tables[t] = {"columns": [], "rows": [], "message": str(exc), "error": True}
    return JSONResponse({
        "job_id": job_id,
        "session_id": session_id,
        "state": final_status_obj.get("state"),
        "tables": results_tables,
        "log": results_obj.get("log"),
        "error": results_obj.get("error")
    })

frontend_build_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build')
from fastapi.staticfiles import StaticFiles

# Serve React build (HTML + static) for all other routes
app.mount(
    "/",
    StaticFiles(directory=frontend_build_dir, html=True),
    name="static",
)
