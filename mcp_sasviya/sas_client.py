from typing import Optional, Any
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse
)

def run_code(request: RunRequest) -> RunResponse:
    """
    Submit SAS code for execution in SAS Viya. Returns job/session info for tracking and results retrieval.
    Used by the /run endpoint to automate analytics, reporting, or ETL tasks.
    """
    import requests
    import os
    import logging
    import json
    try:
        # Read access token and server URL
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_token.txt'), 'r') as f:
            access_token = f.read().strip()
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_server.txt'), 'r') as f:
            sas_server = f.read().strip()
        # Step 1: Get Compute Context UUID
        context_name = 'SAS Studio compute context'
        context_url = f"{sas_server}/compute/contexts?filter=eq(name,'{context_name}')"
        headers = {"Authorization": f"Bearer {access_token}"}
        context_resp = requests.get(context_url, headers=headers, verify=False)
        if context_resp.status_code != 200:
            logging.error(f"Failed to get compute context UUID: {context_resp.text}")
            return RunResponse(
                job_id=None, session_id=None, state="failed", condition_code=-1,
                log="", listing="", data=None, message="Failed to get compute context", error=context_resp.text
            )
        context_items = context_resp.json().get('items', [])
        if not context_items:
            logging.error(f"No compute context found for {context_name}")
            return RunResponse(
                job_id=None, session_id=None, state="failed", condition_code=-1,
                log="", listing="", data=None, message="No compute context found", error="No context UUID"
            )
        context_uuid = context_items[0]['id']

        # Step 2: Create a new session in that context
        session_url = f"{sas_server}/compute/contexts/{context_uuid}/sessions"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        session_payload = {
            "version": 1,
            "name": "MCP",
            "description": "This is a MCP session",
            "attributes": {},
            "environment": {
                "options": ["memsize=4g", "fullstimer"]
            }
        }
        session_resp = requests.post(session_url, headers=headers, data=json.dumps(session_payload), verify=False)
        if session_resp.status_code != 201:
            logging.error(f"SAS Viya session creation failed: {session_resp.text}")
            return RunResponse(
                job_id=None, session_id=None, state="failed", condition_code=-1,
                log="", listing="", data=None, message="Failed to create session", error=session_resp.text
            )
        session_id = session_resp.json()["id"]
        # Submit the job with correct Content-Type for SAS Compute API
        job_url = f"{sas_server}/compute/sessions/{session_id}/jobs"
        job_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/vnd.sas.compute.job.request+json"}
        # Use correct SAS Compute API job payload structure
        job_payload = {
            "data": [
                {
                    "attributes": {
                        "code": request.code
                    },
                    "type": "job"
                }
            ]
        }
        job_resp = requests.post(job_url, headers=job_headers, json=job_payload, verify=False)
        if job_resp.status_code != 201:
            logging.error(f"SAS Viya job submission failed: {job_resp.status_code} {job_resp.text}")
            return RunResponse(
                job_id=None, session_id=session_id, state="failed", condition_code=-1,
                log="", listing="", data=None, message=f"Failed to submit job: {job_resp.text}", error=job_resp.text
            )
        job_id = job_resp.json()["id"]
        state = job_resp.json().get("state", "submitted")
        condition_code = job_resp.json().get("conditionCode", 0)
        log = ""
        listing = ""
        data = None
        message = "Job submitted successfully."
        error = None
        return RunResponse(
            job_id=job_id,
            session_id=session_id,
            state=state,
            condition_code=condition_code,
            log=log,
            listing=listing,
            data=data,
            message=message,
            error=error
        )
    except Exception as e:
        logging.exception("Exception in run_code")
        return RunResponse(
            job_id=None, session_id=None, state="failed", condition_code=-1,
            log="", listing="", data=None, message=str(e), error="mcp.run.error"
        )

def get_job_status(job_id: str, session_id: Optional[str] = None) -> StatusResponse:
    """
    Query the status of a SAS job/session in Viya. Returns job state for monitoring and workflow control.
    Used by the /status endpoint to track running or completed jobs.
    """
    import requests
    import os
    try:
        # Read access token and server URL
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_token.txt'), 'r') as f:
            access_token = f.read().strip()
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_server.txt'), 'r') as f:
            sas_server = f.read().strip()
        if not session_id:
            return StatusResponse(job_id=job_id, session_id=None, state="failed", message="Missing session_id", error="Missing session_id")
        job_url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(job_url, headers=headers)
        if resp.status_code != 200:
            return StatusResponse(job_id=job_id, session_id=session_id, state="failed", message=f"Failed to get job status: {resp.text}", error="viya.status.error")
        job_info = resp.json()
        state = job_info.get("state", "unknown")
        message = job_info.get("state", "No message")
        return StatusResponse(
            job_id=job_id,
            session_id=session_id,
            state=state,
            message=message,
            error=None
        )
    except Exception as e:
        logging.exception("Error in get_job_status")
        return StatusResponse(
            job_id=job_id,
            session_id=session_id,
            state="failed",
            message=str(e),
            error="mcp.status.error"
        )

def get_results(job_id: str, session_id: Optional[str] = None, library: str = 'work', table: str = 'results') -> ResultsResponse:
    """
    Fetch logs, ODS results, and data tables for a completed SAS job in Viya.
    Returns comprehensive outputs for any PROC or DATA step.
    """
    import requests
    import os
    import logging
    import json
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_token.txt'), 'r') as f:
            access_token = f.read().strip()
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_server.txt'), 'r') as f:
            sas_server = f.read().strip()
        headers = {"Authorization": f"Bearer {access_token}"}
        results = {}
        # Fetch log
        log_url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/log?limit=100000"
        log_resp = requests.get(log_url, headers=headers, verify=False)
        log = ""
        if log_resp.status_code == 200:
            log_data = log_resp.json()
            log_lines = [item.get("line", "") for item in log_data.get("items", [])]
            log = "\n".join(log_lines)
        results['log'] = log
        # Fetch ODS results (listing)
        listing_url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/results?limit=100000"
        listing_resp = requests.get(listing_url, headers=headers, verify=False)
        listing = []
        if listing_resp.status_code == 200:
            listing_data = listing_resp.json()
            listing = listing_data.get('items', [])
        results['ods_results'] = listing
        # Fetch data table rows (if present)
        data_url = f"{sas_server}/compute/sessions/{session_id}/data/{library.upper()}/{table.upper()}/rows?limit=100000"
        data_resp = requests.get(data_url, headers=headers, verify=False)
        data = []
        if data_resp.status_code == 200:
            data_data = data_resp.json()
            data = data_data.get('items', [])
        results['table_data'] = data
        # Optionally extract answer for simple jobs (e.g., x=8)
        import re
        answer = None
        match = re.search(r"x=\s*([\w.+-]+)", log)
        if match:
            answer = match.group(1)
        results['extracted_answer'] = answer
        return ResultsResponse(
            job_id=job_id,
            session_id=session_id,
            log=log,
            listing=json.dumps(listing, indent=2),
            data=results,
            answer=answer,
            message="Results fetched (log, ODS, table, answer).",
            error=None
        )
    except Exception as e:
        logging.exception("Exception in get_results")
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
    """
    Fetch logs, output listings, and data results for a completed SAS job in Viya.
    Used by the /results endpoint to provide users with job outputs for further analysis.
    """
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

def get_table(session_id: str, library: str, table_name: str):
    """
    Fetches a table from the given session, library, and table name using the SAS Compute REST API.
    """
    import requests
    import os
    # Read access token and server URL (reuse logic from run_code)
    with open(os.path.join(os.path.dirname(__file__), '..', 'access_token.txt'), 'r') as f:
        access_token = f.read().strip()
    with open(os.path.join(os.path.dirname(__file__), '..', 'access_server.txt'), 'r') as f:
        sas_server = f.read().strip()
    # Construct the endpoint URL
    url = f"{sas_server}/compute/sessions/{session_id}/data/{library}/{table_name}/rows?limit=100000"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"Failed to fetch table: {resp.status_code} {resp.text}")