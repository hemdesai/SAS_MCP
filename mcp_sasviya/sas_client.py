import logging
from typing import Optional, Any
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse
)

def run_code(request: RunRequest) -> RunResponse:
    try:
        # TODO: Implement real SAS Viya session/job submission logic here
        session_id = request.session_id or "session-abc"
        job_id = "job-123"
        state = "completed"
        condition_code = 0
        log = "SAS log output"
        listing = "SAS listing output"
        data = {"result": "Sample result"}
        return RunResponse(
            job_id=job_id,
            session_id=session_id,
            state=state,
            condition_code=condition_code,
            log=log,
            listing=listing,
            data=data,
            message="Job completed successfully.",
            error=None
        )
    except Exception as e:
        logging.exception("Error in run_code")
        return RunResponse(
            job_id=None,
            session_id=request.session_id,
            state="failed",
            condition_code=-1,
            log=None,
            listing=None,
            data=None,
            message=str(e),
            error="mcp.run.error"
        )

def get_status(job_id: str, session_id: Optional[str]) -> StatusResponse:
    try:
        state = "completed"
        return StatusResponse(
            job_id=job_id,
            session_id=session_id,
            state=state,
            message="Job completed.",
            error=None
        )
    except Exception as e:
        logging.exception("Error in get_status")
        return StatusResponse(
            job_id=job_id,
            session_id=session_id,
            state="failed",
            message=str(e),
            error="mcp.status.error"
        )

def get_results(job_id: str, session_id: Optional[str]) -> ResultsResponse:
    try:
        log = "SAS log output"
        listing = "SAS listing output"
        data = {"result": "Sample result"}
        return ResultsResponse(
            job_id=job_id,
            session_id=session_id,
            log=log,
            listing=listing,
            data=data,
            message="Results fetched.",
            error=None
        )
    except Exception as e:
        logging.exception("Error in get_results")
        return ResultsResponse(
            job_id=job_id,
            session_id=session_id,
            log=None,
            listing=None,
            data=None,
            message=str(e),
            error="mcp.results.error"
        )

def cancel_job(request: CancelRequest) -> CancelResponse:
    try:
        state = "cancelled"
        return CancelResponse(
            job_id=request.job_id,
            session_id=request.session_id,
            state=state,
            message="Job cancelled.",
            error=None
        )
    except Exception as e:
        logging.exception("Error in cancel_job")
        return CancelResponse(
            job_id=request.job_id,
            session_id=request.session_id,
            state="failed",
            message=str(e),
            error="mcp.cancel.error"
        )

def check_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="1.0.0",
        message="MCP SAS Viya API is healthy."
    )
    # On error, return a full RunResponse with error info and required fields
    return RunResponse(
        job_id=None,
        session_id=None,
        state="failed",
        condition_code=-1,
        log=None,
            listing=None,
            data=None,
            message=None,
            error=str(e)
        )


def get_compute_context_uuid(access_token, sas_server, context_name="SAS Studio compute context"):
    url = f"{sas_server}/compute/contexts?filter=eq(name,'{context_name}')"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    data = resp.json()
    return data['items'][0]['id'] if data.get("items") else None

def create_sas_session(access_token, sas_server, context_name="SAS Studio compute context"):
    ctx_uuid = get_compute_context_uuid(access_token, sas_server, context_name)
    if not ctx_uuid:
        raise Exception("Could not find compute context UUID")
    url = f"{sas_server}/compute/contexts/{ctx_uuid}/sessions"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.post(url, headers=headers, verify=False)
    print("Status:", resp.status_code, "Content:", resp.text)
    resp.raise_for_status()
    return resp.json()["id"]

def submit_sas_code(session_id, access_token, sas_code, sas_server):
    url = f"{sas_server}/compute/sessions/{session_id}/jobs"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.sas.compute.job.request+json"
    }
    code = sas_code if isinstance(sas_code, str) else "\n".join(sas_code)
    payload = {"code": code}
    logging.debug(f"Submitting SAS code to {url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Payload: {payload}")

    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False)
        logging.debug(f"Job submission response status: {resp.status_code}")
        logging.debug(f"Job submission response content: {resp.text}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error("Error during SAS job submission:")
        logging.error(traceback.format_exc())
        raise

def check_job_submission_status(session_id, job_id, access_token, sas_server):
    url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json().get("state", "unknown")

def get_job_results(session_id, job_id, access_token, result_types, library, table, sas_server):
    results = {}
    if "log" in result_types:
        url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/log"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, verify=False)
        if resp.status_code == 200:
            results["log"] = resp.json().get("log")
    if "results" in result_types:
        url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/results"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, verify=False)
        if resp.status_code == 200:
            results["results"] = resp.json().get("results")
    if "data" in result_types and library and table:
        url = f"{sas_server}/compute/sessions/{session_id}/data/{library.upper()}/{table.upper()}/rows?limit=100000"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, verify=False)
        if resp.status_code == 200:
            results["data"] = resp.json().get("items")
    return results
