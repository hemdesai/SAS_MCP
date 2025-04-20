#!/usr/bin/env python3
import asyncio
from typing import Optional, Any

from mcp.server.fastmcp import FastMCP

import mcp_sasviya.sas_client as client
from mcp_sasviya.schemas import (
    RunRequest, RunResponse, StatusResponse, ResultsResponse,
    CancelRequest, CancelResponse, HealthResponse
)

# Initialize MCP server
mcp = FastMCP(
    name="sas-mcp-server",
    version="1.0.0",
)

# Register tools
@mcp.tool(name="run", description="Run SAS code via SAS Viya")
def run_code(request: RunRequest) -> RunResponse:
    return client.run_code(request)

@mcp.tool(name="status", description="Get SAS job status")
def get_job_status(job_id: str, session_id: Optional[str] = None) -> StatusResponse:
    return client.get_job_status(job_id, session_id)

@mcp.tool(name="results", description="Fetch SAS job results")
def get_results(job_id: str, session_id: Optional[str] = None) -> ResultsResponse:
    return client.get_results(job_id, session_id)

@mcp.tool(name="cancel", description="Cancel a running SAS job")
def cancel_job(request: CancelRequest) -> CancelResponse:
    return client.cancel_job(request)

@mcp.tool(name="table", description="Fetch a table from SAS session")
def get_table(session_id: str, library: str, table_name: str) -> Any:
    return client.get_table(session_id, library, table_name)

@mcp.tool(name="health", description="Health check for SAS MCP server")
def check_health() -> HealthResponse:
    return client.check_health()

# Run server
if __name__ == "__main__":
    asyncio.run(mcp.run())
