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
1. From the `SAS_MCP` directory, set your Python path:
   ```sh
   $Env:PYTHONPATH = $PWD
   ```
2. Start the MCP server:
   ```sh
   mcp dev mcp_sasviya\mcp_server.py
   ```
3. Open [MCP Inspector](https://inspector.modelcontext.org/) in your browser.
4. At the prompt, enter: `mcp`
5. Use arguments: `run mcp_sasviya/mcp_server.py`
6. Ensure `PYTHONPATH` is set if needed.
7. In the Inspector UI, go to **Tools** → **List Tools**.
8. Click **Run** to execute SAS code via the `run` tool or explore other available tools (`status`, `results`, `table`, `health`).

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

## Instructions for Using MCP Inspector (VS Code + Browser)
1) Run from `SAS_MCP` directory: `$Env:PYTHONPATH = $PWD`
2) Start the server: `mcp dev mcp_sasviya\mcp_server.py`
3) Open [MCP Inspector](https://inspector.modelcontext.org/) in your browser.
4) At the prompt, enter: `mcp`
5) Use arguments: `run mcp_sasviya/mcp_server.py`
6) Ensure `PYTHONPATH` is set to your project root if needed.
7) In the Inspector UI, go to **Tools** → **List Tools**.
8) Click **Run** to invoke the `run` tool and start executing SAS code.

---

## Areas for Future Development
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
Please open issues or pull requests on [GitHub](https://github.com/hemdesai/SAS_MCP).