# MCP SAS Viya Server (MCP/STDIO Edition)

**Executive Summary:**
This repository delivers a production-ready, MCP-compliant SAS Viya server that enables any AI agent, LLM, or orchestration platform to securely run, monitor, and retrieve SAS analytics jobs using the Model Context Protocol (MCP) over standard input/output (STDIO). No REST APIs, containers, or frontends required—just pure, agent-driven analytics automation.

---

## What Does This Server Do?
- **Exposes SAS analytics as MCP tools**: Run code, fetch results, check status, retrieve tables, and more.
- **Native MCP/STDIO protocol**: Seamless integration with LLMs, the MCP Inspector, and agent frameworks.
- **LLM/AI Ready**: Lets AI agents programmatically decide, submit, and retrieve SAS jobs and data.

---

## Key Features
- **MCP Protocol (STDIO) Only**: No REST, no HTTP, no containers—just pure MCP for maximum compatibility with AI/LLM workflows.
- **Tool-based Design**: All SAS operations are registered MCP tools (e.g., `run`, `status`, `results`, `table`, `health`).
- **Structured Output**: Results are returned as clean, developer/LLM-friendly JSON.
- **Session Management**: Tables and outputs are session-scoped for reliability.
- **Tested with MCP Inspector**: Fully validated for agent-driven workflows.

---

## How to Use (MCP Inspector or LLM/Agent)
1. **Start the MCP server**:
   ```sh
   python mcp_sasviya/mcp_server.py
   ```
2. **Open [MCP Inspector](https://inspector.modelcontext.org/) or connect your LLM/agent.**
3. **Choose STDIO as transport.**
4. **List and call tools** (e.g., `run`, `status`, `results`, `table`, `health`).

---

## Example: Multi-step SAS Workflow
```sas
/* Step 1: Create a table */
data work.results1;
  length name $16;
  id=1; name='Alice'; salary=50000+5000; output;
  id=2; name='Bob'; salary=.; output;
  id=3; name='Charlie'; salary=60000*1.05; output;
run;

/* Step 2: Summary statistics */
proc means data=work.results1 n mean std min max;
  var salary;
  output out=work.results2;
run;
```
- Use the `run` tool to submit code.
- Wait for completion (`status`).
- Fetch results with the `results` tool or retrieve tables (`table`).

---

## Available Tools (MCP)
| Tool       | Description                      |
|------------|----------------------------------|
| run        | Submit SAS code for execution    |
| status     | Check job/session status         |
| results    | Fetch logs/output for a job      |
| table      | Retrieve a table by name         |
| cancel     | Cancel a running job             |
| health     | Server health check              |

---

## Best Practices & Limitations
- **Always write output to a table** (e.g., `work.results1`). Only tables can be fetched.
- **Wait for job completion** before fetching tables (check `status`).
- **Character variables**: Use `length varname $N;` to avoid truncation.
- **Dates**: Use `put(datevar, yymmdd10.);` for readable output.
- **Session scope**: Tables exist only within the session/job that created them.

---

## Project Structure
```
SAS_MCP/
├── mcp_sasviya/
│   ├── mcp_server.py    # MCP stdio server (entrypoint)
│   ├── sas_client.py    # SAS Viya integration logic
│   ├── schemas.py       # Pydantic schemas for requests/responses
│   └── ...
├── test_scripts/        # (Archived) Example/test scripts
├── archive/             # (Archived) Docker, frontend, etc.
├── requirements.txt
└── README.md
```

---

## How to Run

Install dependencies:
```sh
pip install -r requirements.txt
```

Start the MCP server:
```sh
python mcp_sasviya/mcp_server.py
```

---

## MCP Inspector Quickstart
1. Start the server: `python mcp_sasviya/mcp_server.py`
2. Open MCP Inspector in your browser.
3. Set `Transport Type` to STDIO.
4. Command: `mcp`
5. Arguments: `run mcp_sasviya/mcp_server.py`
6. List tools, call `run`, `status`, `results`, `table`, etc.

---

## Roadmap
- **Persistent storage** (future)
- **Advanced logging/metrics** (future)
- **Natural language/LLM agent integration** (future)

---

## License
MIT (or specify your license here)

---

## Contributing
Contributions and feedback are welcome!  
Open issues or pull requests on [GitHub](https://github.com/hemdesai/SAS_MCP).

---

## ⚠️ IMPORTANT: How to Retrieve Results from SAS Jobs

### Example: Multiple Outputs in One Job

```sas
data work.results1;
  length name $16;
  id=1; name='Alice'; salary=50000+5000; output;
  id=2; name='Bob'; salary=.; output;
  id=3; name='Charlie'; salary=60000*1.05; output;
run;

proc means data=work.results1 n mean std min max;
  var salary;
  output out=work.results2;
run;
```
- Fetch `results1` for raw data, `results2` for summary stats.

---

## Key Features

- Unified REST API for SAS Viya code execution and data retrieval.
- Supports multiple output tables per job; fetch each by name.
- Clean JSON output:
  ```json
  {
    "columns": ["id", "name", "salary", ...],
    "rows": [[1, "Alice", 55000, ...], ...]
  }
  ```
- Handles missing values, character truncation, and SAS date formatting (with recommended SAS code).
- Session-based: tables are tied to the session in which they were created.
- Extensible for more advanced analytics and workflows.
- Compatible with MCP Inspector UI for interactive testing and debugging.

---

## Tools & Functionality

| Functionality           | Endpoint   | What It Does                                         | Status                |
|------------------------|------------|------------------------------------------------------|-----------------------|
| **Run SAS Code**       | `/run`     | Submit SAS code for execution and get a job ID        | ✅ Ready              |
| **Check Job Status**   | `/status`  | Get the current state of a submitted SAS job          | ✅ Ready              |
| **Fetch Table**        | `/table`   | Retrieve any output table by name                     | ✅ Ready              |
| **Cancel a Job**       | `/cancel`  | Stop a SAS job that is currently executing            | ✅ Ready              |
| **Health Check**       | `/health`  | Confirm the MCP server is running                     | ✅ Ready              |
| **Inspector UI**       | `/`        | Interactive UI for code submission and results display | ✅ Ready              |

---

## Usage

### 1. Start the MCP Server
```sh
$Env:PYTHONPATH = $PWD
mcp dev mcp_sasviya\mcp_server.py
```

### 2. Connect via MCP Inspector
- Open MCP Inspector in your browser.
- Use the command: `mcp`
- Arguments: `run mcp_sasviya/mcp_server.py`
- Set environment variables as needed (e.g., `PYTHONPATH`).

### 3. Submit SAS Code
- Use the `run` tool with JSON input:
  ```json
  {
    "code": "data work.results1; ... run; proc means data=work.results1 ... output out=work.results2; run;"
  }
  ```

### 4. Retrieve Results
- Use the `table` tool with:
  - `session_id`: (from run tool result)
  - `library`: `work`
  - `table_name`: `results1`, `results2`, etc.

---

## Limitations

- Only tables (datasets) in the specified session/library are accessible.
- No support for direct ODS/listing/log output retrieval.
- Session cleanup and resource management are manual (unless automated in your workflow).

---

## Developer Notes

- Tools are registered using the MCP protocol, following the same conventions as the GitHub MCP server.
- All request/response schemas are defined in `mcp_sasviya/schemas.py` using Pydantic.
- The server is compatible with FastAPI and can be deployed as a container or on Kubernetes.
- Error handling and logging are implemented throughout for reliability.

---

## Troubleshooting

- If you see validation errors, ensure your JSON input is correctly formatted.
- If table output is truncated, increase the SAS variable length in your code.
- If you cannot fetch a table, make sure it was created in the same session and not deleted.

---

## Contributing

- Fork the repo and submit PRs for enhancements or bugfixes.
- Follow the existing schema and tool registration patterns.
- Keep the README updated with any new features or changes.

---

## License

MIT (or your chosen license)

| **React Front-end**    | `/`        | Interactive UI for code submission and results display | ✅ Ready              |
| **LLM Interface**      | `/llm`     | Natural language to SAS code (future)                 | 🚧 **WORK IN PROGRESS** |
| **Authentication**     | -          | OAuth/token-based endpoint security                   | 🚫 **Not Being Developed in this MVP** |
| **Persistent Storage** | -          | Database or file-based result persistence             | 🚧 **WORK IN PROGRESS** |
| **Advanced Logging**   | -          | Structured logs, metrics, admin UI, observability     | 🚧 **WORK IN PROGRESS** |

---

## How it Works

Typical workflow for using the MCP SAS Viya API:

1. **Submit SAS code** to `/run` and receive a `job_id`.
2. **Check status** of the job using `/status?job_id=...`.
3. **Once complete, fetch results** using `/results?job_id=...`.
4. **If needed, cancel a job** using `/cancel`.

---

## Example Usage

### 1. Run SAS Code
**Request:**
```json
POST /run
{
  "code": "data _null_; put 'Hello, world!'; run;"
}
```
**Response:**
```json
{
  "job_id": "job-123",
  "session_id": "session-abc",
  "state": "completed",
  "condition_code": 0,
  "log": "SAS log output",
  "listing": "SAS listing output",
  "data": {"result": "Sample result"},
  "message": "Job completed successfully.",
  "error": null
}
```

### 2. Check Job Status
**Request:**
```
GET /status?job_id=job-123
```
**Response:**
```json
{
  "job_id": "job-123",
  "session_id": null,
  "state": "completed",
  "message": "Job completed.",
  "error": null
}
```

### 3. Fetch Results
**Request:**
```
GET /results?job_id=job-123
```
**Response:**
```json
{
  "job_id": "job-123",
  "session_id": null,
  "log": "SAS log output",
  "listing": "SAS listing output",
  "data": {"result": "Sample result"},
  "message": "Results fetched.",
  "error": null
}
```

### 4. Cancel a Job
**Request:**
```json
POST /cancel
{
  "job_id": "job-123",
  "session_id": null
}
```
**Response:**
```json
{
  "job_id": "job-123",
  "session_id": null,
  "state": "cancelled",
  "message": "Job cancelled.",
  "error": null
}
```

### 5. Health Check
**Request:**
```
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "message": "MCP SAS Viya API is healthy."
}
```

---

## Front-end Application

To run the React front-end:

```sh
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the UI.

For a production build:

```sh
npm run build
```

---

## Project Structure

```
SAS_MCP/
├── mcp_sasviya/
│   ├── main.py          # FastAPI app and endpoints
│   ├── schemas.py       # Pydantic models (MCP schema)
│   ├── sas_client.py    # SAS Viya API integration logic (stubbed)
│   └── ...
├── frontend/            # React front-end application
├── deploy.yaml          # Kubernetes Deployment manifest
├── service.yaml         # Kubernetes Service manifest
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Instructions of using MCP Inspector to test (VS code + browser)
1) Run from SAS_MCP directory: `$Env:PYTHONPATH = $PWD`
2) Run from SAS_MCP directory: `mcp dev mcp_sasviya\mcp_server.py`
3) Open MCP Inspector in your browser.
4) Use the command: `mcp`
5) Arguments: `run mcp_sasviya/mcp_server.py` (not mcp_sasviya\mcp_server)
6) Set environment variables as needed (e.g., `PYTHONPATH`).
7) Got to Tools on Top & List Tools
8) Click "Run" to start the server.


---

## Areas for Future Development

- **LLM/AI Integration:** Natural language interface for code generation and results interpretation (**WIP**)
- **Persistent Storage:** Integrate a database for job/data persistence (**WIP**)
- **Advanced Logging & Observability:** Metrics, tracing, and admin UI (**WIP**)
- **Authentication:** OAuth/token-based security (Not planned for this MVP)
- **CI/CD Automation:** GitHub Actions for automated build and deployment (**WIP**)

---

## License

MIT (or specify your license here)

---

## Contributing

Contributions and feedback are welcome!  
Please open issues or pull requests on [GitHub](https://github.com/hemdesai/SAS_MCP).

---