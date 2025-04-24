# SAS MCP Chatbot Demo (Streamlit, GPT 4.1 Mini, MCP Orchestration)

This project is a demo of a Streamlit-based chatbot UI that interacts with a FastAPI backend, executing SAS code jobs using the Model Context Protocol (MCP). All SAS operations are routed through MCP tools only; no direct SAS client calls are made. Only valid SAS code jobs are supported—no llm/ local or non-SAS math operations.

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
- **Demo UI**: Uses Streamlit for the chatbot interface.
- **LLM/Prompts**: Uses OpenAI GPT-4.1-mini for prompt classification (all SAS code is routed through MCP).

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
4. Start the Streamlit frontend (from project root):
   ```sh
   streamlit run frontend/chatbot_demo.py
   ```
5. Open [http://localhost:8501](http://localhost:8501) in your browser.
6. Enter valid SAS code in the chat UI. Specify the output table name (e.g., `results2`) in the single Table Name input to fetch the correct results. Only one Table Name input is used and honored. The UI and backend always use the Table Name input as provided by the user.
7. All results are fetched via MCP tools and the MCP tool call trace is shown after each response.

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

The Streamlit frontend provides a chat interface for users to interact with the SAS MCP backend. Users can enter SAS code, and the backend executes via MCP tools, returning results and MCP tool traces. Only SAS code jobs are supported.

---

## Backend Logic / MCP Orchestration

The FastAPI backend uses the MCP tool layer for all SAS operations. Tools like `run_code`, `get_table`, and `get_results` are invoked for every user request, and each tool logs its invocation for traceability. No SAS client calls bypass MCP. Only valid SAS code jobs are accepted; local or non-SAS operations are not supported.

---

## Troubleshooting

* Make sure to set the Python path correctly before starting the FastAPI backend.
* Check the console logs for any errors or warnings.
* If you encounter issues with the React frontend, try restarting the development server.
- Always write output to a table (e.g., `work.results`). Only tables can be fetched.
- Wait for job completion before fetching tables.
- Use `length varname $N;` for character variables to avoid truncation.
- Use `put(datevar, yymmdd10.);` for readable dates.
- Tables exist only within the session/job that created them.

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

## Key Features

- All SAS operations are routed through MCP tools only (no direct SAS client calls).
- Supports multiple output tables per job; fetch each by name.
- Clean JSON output for results.
- Handles missing values, character truncation, and SAS date formatting (with recommended SAS code).
- Session-based: tables are tied to the session in which they were created.
- Extensible for advanced analytics and workflows.
- Compatible with MCP Inspector UI for interactive testing and debugging.

---

## Roadmap
- **Persistent storage** (future)
- **Advanced logging/metrics** (future)
- **Further Natural language/LLM agent integration** (future)

---

## License
MIT (or specify your license here)

---

## Contributing
Contributions and feedback are welcome!  
Please open issues or pull requests on [GitHub](https://github.com/hemdesai/SAS_MCP).
