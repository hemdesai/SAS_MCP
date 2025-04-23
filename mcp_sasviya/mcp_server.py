#!/usr/bin/env python3
import asyncio
from typing import Optional, Any

from mcp.server.fastmcp import FastMCP

import mcp_sasviya.sas_client as client
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse, ContextResponse, TableResponse
)

# In-memory session context
session_context = {}

# Initialize MCP server
mcp = FastMCP(
    name="sas-mcp-server",
    version="1.0.0",
)

# Register tools
import re

def parse_addition_prompt(text):
    import re
    numbers = [int(x) for x in re.findall(r"\d+", text)]
    sas_code = f"data work.results; sum = {'+'.join(map(str, numbers))}; run;"
    return numbers, sas_code

@mcp.tool(name="run", description="Run SAS code or prompt")
def run_code(request: RunRequest) -> RunResponse:
    import logging
    logging.info(f"[MCP TOOL] run_code called with session_id={getattr(request, 'session_id', None)}")
    """
    MCP tool: Submit SAS code or math prompt via MCP for execution in SAS Viya. Returns job status and details. All orchestration is via MCP tools only.
    """
    import re
    session_id = getattr(request, 'session_id', None)
    code = getattr(request, 'code', None)
    ctx = session_context.setdefault(session_id, {}) if session_id else {}
    # Always rewrite math prompts and simple data steps to work.results.x for demo consistency
    if isinstance(code, str):
        code_stripped = code.strip().lower()
        # Handle 'add' prompt
        if code_stripped.startswith("add"):
            numbers = [int(x) for x in re.findall(r"\d+", code)]
            if numbers:
                sas_code = f"data work.results; x={' + '.join(map(str, numbers))}; output; run;"
                request.code = sas_code
                ctx['last_code'] = sas_code
        # Handle simple data step with assignment but not to x
        elif re.match(r"data work\.results;.*=.*;.*output;.*run;", code_stripped, re.DOTALL):
            # Replace any assignment to ensure variable is 'x'
            expr_match = re.search(r"data work\.results;\s*(\w+)\s*=([^;]+);\s*output;\s*run;", code_stripped, re.DOTALL)
            if expr_match:
                expr = expr_match.group(2).strip()
                sas_code = f"data work.results; x = {expr}; output; run;"
                request.code = sas_code
                ctx['last_code'] = sas_code
        else:
            if session_id:
                ctx['last_code'] = code
    # Context-aware chaining for prompts like 'add 3 more'
    if isinstance(code, str) and code.strip().lower().startswith("add"):
        match = re.search(r"add (\d+)", code.strip().lower())
        if match and session_id:
            add_value = int(match.group(1))
            last_table = ctx.get('last_table')
            if last_table and last_table.get('rows') and last_table['rows'][0]:
                prev_x = last_table['rows'][0][0]
                sas_code = f"data work.results; x={prev_x}+{add_value}; output; run;"
                ctx['last_code'] = sas_code
                request.code = sas_code
            ctx['last_code'] = code
    return client.run_code(request)

@mcp.tool(name="status", description="Get SAS job status")
def get_job_status(job_id: str, session_id: Optional[str] = None) -> StatusResponse:
    """
    Retrieves the status of a SAS job in a SAS Viya compute session using the job and session IDs. Returns the current job state (e.g., running, completed, failed) and error details if applicable.
    """
    return client.get_job_status(job_id, session_id)

@mcp.tool(name="results", description="Fetch SAS job results")
def get_results(job_id: str, session_id: Optional[str] = None) -> ResultsResponse:
    import logging
    logging.info(f"[MCP TOOL] get_results called with job_id={job_id}, session_id={session_id}")
    """
    Retrieves the results of a previously executed SAS job from a SAS Viya compute session using job and session IDs. Returns logs, ODS output, tables, and error messages as a JSON object.
    """
    return client.get_results(job_id, session_id)

@mcp.tool(name="cancel", description="Cancel SAS job")
def cancel_job(request: CancelRequest) -> CancelResponse:
    import logging
    logging.info(f"[MCP TOOL] cancel_job called with job_id={getattr(request, 'job_id', None)}, session_id={getattr(request, 'session_id', None)}")
    """
    Cancels a running SAS job in a SAS Viya compute session using the job and session IDs. Returns confirmation or error details.
    """
    return client.cancel_job(request)

@mcp.tool(name="table", description="Fetch table from session")
def get_table(session_id: str, library: str, table_name: str) -> TableResponse:
    import logging
    logging.info(f"[MCP TOOL] get_table called with session_id={session_id}, library={library}, table_name={table_name}")
    """
    Fetches a table from a SAS Viya compute session using session ID, library, and table name. Returns columns, rows, and error info as a JSON object.
    """
    result = client.get_table(session_id, library, table_name)
    ctx = session_context.setdefault(session_id, {})
    ctx['last_table'] = result
    # Store all tables by name for context-aware chaining
    tables = ctx.setdefault('tables', {})
    tables[table_name] = result
    # Optionally, add to history
    history = ctx.setdefault('history', [])
    history.append({"action": "table", "table_name": table_name, "result": result})
    return result

@mcp.tool(name="context", description="Show session context")
def show_context(session_id: str) -> ContextResponse:
    import logging
    logging.info(f"[MCP TOOL] show_context called with session_id={session_id}")
    """
    Returns the full context (history, variables, results, etc.) stored for the given session_id as a JSON object. Useful for debugging, demos, and understanding session state.
    """
    ctx = session_context.get(session_id, {})
    return ContextResponse(
        session_id=session_id,
        history=ctx.get("history"),
        variables=ctx.get("variables"),
        last_result=ctx.get("last_result"),
    )

@mcp.tool(name="health", description="Health check")
def check_health() -> HealthResponse:
    import logging
    logging.info("[MCP TOOL] check_health called")
    """
    Checks the health and availability of the SAS MCP server. Returns status and version info.
    """
    return client.check_health()

# Run server
if __name__ == "__main__":
    asyncio.run(mcp.run())
