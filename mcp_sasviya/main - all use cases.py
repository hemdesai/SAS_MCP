from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .sas_client import run_sas_job
from .schemas import MCPRequest, MCPResponse
import logging, traceback

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="MCP SAS Viya Service", version="0.1")

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc()
        },
    )

@app.get("/status")
def status():
    return {"status": "ok"}

@app.post("/run", response_model=MCPResponse)
def run(request: MCPRequest):
    result = run_sas_job(request)
    return result

@app.post("/run")
async def run_sas_job(request: RunRequest):  # Adjust signature as needed
    logging.info(f"Received /run request: {request}")
    try:
        # ... (your logic to create session, etc.)
        result = submit_sas_code(session_id, access_token, request.sas_code, sas_server)
        logging.info(f"SAS job result: {result}")
        # ... (your logic to fetch logs/results, etc.)
        return {"result": result}  # Adjust as needed
    except Exception as e:
        logging.error("Exception in /run endpoint:")
        logging.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )