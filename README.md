# React front end chatbot (not LLM) - SAS MCP demo

This branch contains a demo of a React-based chatbot UI that interacts with a FastAPI backend to execute SAS code using the Model Context Protocol (MCP). No LLMs or GenAI are used for conversation or code generation; all math and SAS execution is handled by SAS MCP.

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

## How to Use This Demo

1. Clone this branch and install dependencies:
   ```sh
   pip install -r requirements.txt
   cd archive/frontend
   npm install
   ```
2. Set your Python path (PowerShell):
   ```sh
   $Env:PYTHONPATH = $PWD
   ```
3. Start the FastAPI backend (from project root):
   ```sh
   uvicorn mcp_sasviya.main:app --reload --port 8000
   ```
4. Start the React frontend (in `archive/frontend`):
   ```sh
   npm start
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser.
6. Enter SAS code or math prompts in the chat UI. To fetch tables, include a line like `Tables: results1, results2` at the end of your message.

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
| Tool       | Description                          |
|------------|------------------------------------|
| run        | Submit SAS code for execution      |
| status     | Check job/session status           |
| results    | Fetch logs/output for a job        |
| table      | Retrieve a table by name           |
| cancel     | Cancel a running job               |
| health     | Server health check                |
| context    | Retrieve full session context      |

---

## UI Details

The React frontend provides a simple chat interface for users to interact with the SAS MCP backend. Users can enter SAS code or math prompts, and the backend will execute the code and return the results in a clean, JSON format.

---

## Backend Logic (Table Extraction)

The FastAPI backend uses the SAS Viya integration logic to execute SAS code and extract tables from the results. The `table` tool allows users to retrieve tables by name, and the `results` tool returns the logs/output for a job.

---

## Troubleshooting

* Make sure to set the Python path correctly before starting the FastAPI backend.
* Check the console logs for any errors or warnings.
* If you encounter issues with the React frontend, try restarting the development server.
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