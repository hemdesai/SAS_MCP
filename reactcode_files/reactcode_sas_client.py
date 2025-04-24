from typing import Optional, Any, Dict
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse
)

def run_code(request: RunRequest) -> RunResponse:
    import requests, os, json, logging
    try:
        base = os.path.dirname(__file__)
        with open(os.path.join(base, '..', 'access_token.txt'), 'r') as f:
            access_token = f.read().strip()
        with open(os.path.join(base, '..', 'access_server.txt'), 'r') as f:
            sas_server = f.read().strip()
        ctx_url = f"{sas_server}/compute/contexts?filter=eq(name,'SAS Studio compute context')"
        hdr = {'Authorization': f'Bearer {access_token}'}
        r = requests.get(ctx_url, headers=hdr, verify=False)
        if r.status_code != 200:
            return RunResponse(job_id=None, session_id=None, state='failed', condition_code=-1, log='', listing='', data=None, message='Failed compute context', error=r.text)
        items = r.json().get('items', [])
        if not items:
            return RunResponse(job_id=None, session_id=None, state='failed', condition_code=-1, log='', listing='', data=None, message='No compute context found', error='No context')
        ctx_id = items[0]['id']
        sess_url = f"{sas_server}/compute/contexts/{ctx_id}/sessions"
        sess_hdr = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        sess_pl = {
            'version': 1,
            'name': 'MCP',
            'description': 'This is a MCP session',
            'attributes': {},
            'environment': {'options': ['memsize=4g', 'fullstimer']}
        }
        r2 = requests.post(sess_url, headers=sess_hdr, data=json.dumps(sess_pl), verify=False)
        if r2.status_code != 201:
            return RunResponse(job_id=None, session_id=None, state='failed', condition_code=-1, log='', listing='', data=None, message='Failed create session', error=r2.text)
        session_id = r2.json().get('id')
        job_url = f"{sas_server}/compute/sessions/{session_id}/jobs"
        job_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        code_lines = request.code.split("\n") if isinstance(request.code, str) else request.code
        job_payload = {
            "version": 1,
            "name": "MCP",
            "description": "Submitting code from MCP",
            "code": code_lines,
            "attributes": {"resetLogLineNumbers": True}
        }
        job_resp = requests.post(job_url, headers=job_headers, json=job_payload, verify=False)
        if job_resp.status_code != 201:
            logging.error(f"SAS Viya job submission failed: {job_resp.status_code} {job_resp.text}")
            return RunResponse(
                job_id=None, session_id=session_id, state="failed", condition_code=-1,
                log="", listing="", data=None, message=f"Failed to submit job: {job_resp.text}", error=job_resp.text
            )
        resp_json = job_resp.json()
        job_id = resp_json.get("id")
        state = resp_json.get("state", "submitted")
        condition_code = resp_json.get("conditionCode", 0)
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
        logging.exception('Exception in run_code')
        return RunResponse(job_id=None, session_id=None, state='failed', condition_code=-1, log='', listing='', data=None, message=str(e), error='mcp.run.error')

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
        # Fetch log
        log_url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/log?limit=100000"
        log_resp = requests.get(log_url, headers=headers, verify=False)
        log = ""
        if log_resp.status_code == 200:
            log_data = log_resp.json()
            log_lines = [item.get("line", "") for item in log_data.get("items", [])]
            log = "\n".join(log_lines)
        # Fetch ODS results (listing)
        listing_url = f"{sas_server}/compute/sessions/{session_id}/jobs/{job_id}/results?limit=100000"
        listing_resp = requests.get(listing_url, headers=headers, verify=False)
        listing = []
        if listing_resp.status_code == 200:
            listing_data = listing_resp.json()
            listing = listing_data.get('items', [])
        # Fetch table using get_table
        from mcp_sasviya.sas_client import get_table
        table_json = get_table(session_id, library, table)
        # Optionally extract answer for simple jobs (e.g., x=8)
        import re
        answer = None
        match = re.search(r"x=([\d+\-*/.]+)", log)
        if match:
            answer = match.group(1)
        return ResultsResponse(
            job_id=job_id,
            session_id=session_id,
            log=log,
            listing=json.dumps(listing, indent=2),
            data=table_json,
            answer=answer,
            message="Results fetched (log, ODS, table, answer).",
            error=None
        )
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

def get_table(session_id: str, library: str, table_name: str) -> Dict[str, Any]:
    """
    Enhanced table fetch: returns columns and rows in a user-friendly JSON format.
    """
    import requests, os, logging
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_token.txt'), 'r') as f:
            access_token = f.read().strip()
        with open(os.path.join(os.path.dirname(__file__), '..', 'access_server.txt'), 'r') as f:
            sas_server = f.read().strip()
        # Fetch column metadata
        col_url = f"{sas_server}/compute/sessions/{session_id}/data/{library}/{table_name}/columns"
        headers = {"Authorization": f"Bearer {access_token}"}
        col_resp = requests.get(col_url, headers=headers, verify=False)
        if col_resp.status_code != 200:
            return {
                "columns": [],
                "rows": [],
                "message": f"Failed to fetch column metadata: {col_resp.text}",
                "error": col_resp.text
            }
        columns = [col['name'] for col in col_resp.json().get('items', [])]
        # Fetch rows
        row_url = f"{sas_server}/compute/sessions/{session_id}/data/{library}/{table_name}/rows?limit=100000"
        row_resp = requests.get(row_url, headers=headers, verify=False)
        if row_resp.status_code != 200:
            return {
                "columns": columns,
                "rows": [],
                "message": f"Failed to fetch table rows: {row_resp.text}",
                "error": row_resp.text
            }
        items = row_resp.json().get('items', [])
        rows = [item['cells'] for item in items]
        return {
            "columns": columns,
            "rows": rows,
            "message": "Table fetched successfully",
            "error": None
        }
    except Exception as e:
        logging.exception("Exception in get_table")
        return {
            "columns": [],
            "rows": [],
            "message": str(e),
            "error": "mcp.table.error"
        }
