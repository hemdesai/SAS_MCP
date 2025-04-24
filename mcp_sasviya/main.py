# Restriction: Only SAS code jobs are supported. No local or non-SAS operations.
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, responses, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse, ErrorResponse, TableResponse
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
    response = sas_client.get_job_status(job_id, session_id)
    if response.state == "failed" or not response.job_id or not response.session_id:
        raise HTTPException(status_code=400, detail=response.message or "Missing job_id or session_id")
    return response

@api_router.get("/results", response_model=ResultsResponse, responses={400: {"model": ErrorResponse}})
async def results(job_id: str = Query(..., description="Job identifier"), session_id: Optional[str] = Query(None, description="Session ID (optional)")):
    response = sas_client.get_results(job_id, session_id)
    if response.error or not response.job_id or not response.session_id:
        raise HTTPException(status_code=400, detail=response.message or "Missing job_id or session_id")
    return response

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
    response = sas_client.run_code(request)
    if response.state == "failed" or not response.job_id or not response.session_id:
        raise HTTPException(status_code=400, detail=response.message or "Missing job_id or session_id")
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
    if not session_id or not table_name:
        raise HTTPException(status_code=400, detail="Missing session_id or table_name")
    try:
        table_data = mcp_server.get_table(session_id, library, table_name)
        if isinstance(table_data, TableResponse):
            return {"columns": table_data.columns, "rows": table_data.rows, "message": table_data.message, "error": table_data.error}
        else:
            return table_data if isinstance(table_data, dict) else table_data.__dict__
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
    # Always use library and table_name from frontend if provided
    library = data.get("library") or "work"
    table_name = data.get("table_name")
    tables = []
    if table_name:
        tables = [table_name]
    else:
        # Fallback: extract from prompt or use defaults
        if prompt:
            match = re.search(r"Tables:\s*(.*)", prompt, re.IGNORECASE)
            if match:
                table_line = match.group(1)
                tables = [t.strip() for t in table_line.split(",") if t.strip()]
        if not tables:
            tables = ["results", "results1", "results2"]
    mcp = mcp_server.mcp
    import json
    import logging
    # Classify prompt via MCP tool
    classify_resp = await mcp.call_tool("classify", {"text": prompt})
    # extract prompt_type
    if isinstance(classify_resp, list) and classify_resp:
        cr = classify_resp[0]
    else:
        cr = classify_resp
    if isinstance(cr, dict):
        prompt_type = cr.get("type", "sas")
    elif hasattr(cr, "type"):
        prompt_type = cr.type
    elif hasattr(cr, "text"):
        try:
            prompt_type = json.loads(cr.text).get("type", "sas")
        except:
            prompt_type = "sas"
    else:
        prompt_type = "sas"
    # Engine selection: Local vs SAS for math prompts only
    math_engine = data.get("math_engine", "Local").lower()
    if prompt_type == "math" and math_engine == "local":
        import re
        nums = [int(n) for n in re.findall(r"\d+", prompt)]
        total = sum(nums)
        tbl = tables[0] if tables else "results"
        result = {"columns": ["x"], "rows": [[total]], "message": "Computed locally", "error": False}
        return JSONResponse({"job_id": None, "session_id": None, "state": "completed", "tables": {tbl: result}, "log": "", "error": None, "type": "math"})
    # For math prompts routed to SAS or any SAS code: convert simple additions if math_engine is SAS
    if prompt_type == "math" and math_engine == "sas":
        from mcp_sasviya.mcp_server import parse_addition_prompt
        try:
            _, sas_code = parse_addition_prompt(prompt)
            prompt = sas_code
            tables = [table_name] if table_name else ["results"]
            prompt_type = "sas"
        except:
            pass
    run_req = {"request": {"code": prompt, "session_id": session_id}}
    try:
        run_resp = await mcp.call_tool("run", run_req)
        logging.warning(f"run_resp: {run_resp} (type: {type(run_resp)})")
        # Robust extraction of job_id/session_id from TextContent
        resp_dict = {}
        if isinstance(run_resp, list) and run_resp:
            first = run_resp[0]
            if hasattr(first, "text") and isinstance(first.text, str):
                try:
                    resp_dict = json.loads(first.text)
                except Exception as e:
                    logging.error(f"Failed to parse run_resp[0].text: {e}")
                    resp_dict = {}
        elif hasattr(run_resp, "dict"):
            resp_dict = run_resp.dict()
        elif isinstance(run_resp, dict):
            resp_dict = run_resp
        elif hasattr(run_resp, "text"):
            try:
                resp_dict = json.loads(run_resp.text)
            except Exception as e:
                logging.error(f"Failed to parse run_resp.text: {e}")
                resp_dict = {}
        job_id = resp_dict.get('job_id')
        session_id = resp_dict.get('session_id')
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
        results_tables = {}
        # Always use MCP server get_table for all fetches
        for t in tables:
            if session_id and t:
                try:
                    tbl_obj = mcp_server.get_table(session_id, library, t)
                    if isinstance(tbl_obj, TableResponse):
                        results_tables[t] = {"columns": tbl_obj.columns, "rows": tbl_obj.rows, "message": tbl_obj.message, "error": tbl_obj.error}
                    else:
                        results_tables[t] = tbl_obj if isinstance(tbl_obj, dict) else tbl_obj.__dict__
                except Exception as exc:
                    results_tables[t] = {"columns": [], "rows": [], "message": str(exc), "error": True}
        # Return tables in response
        return JSONResponse({
            "job_id": job_id,
            "session_id": session_id,
            "state": final_status_obj.get("state", None),
            "tables": results_tables,
            "log": getattr(run_resp, "log", ""),
            "error": getattr(run_resp, "error", None),
            "type": "sas"
        })
    except Exception as e:
        return JSONResponse({"job_id": None, "session_id": None, "state": "failed", "tables": {}, "log": "", "error": str(e), "type": "sas"})
