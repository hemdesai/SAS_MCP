# MCP SAS Viya API

A cloud-ready, standardized Managed Compute Platform (MCP) API for submitting, tracking, and retrieving SAS Viya jobs.  
Built for extensibility, observability, and seamless integration with modern cloud-native workflows.

---

# Overview

The MCP SAS Viya API provides a unified interface for executing SAS code, managing sessions and jobs, and retrieving results from a SAS Viya environment.  
Designed for reliability and scalability, it uses FastAPI, Pydantic schemas, and is optimized for Kubernetes deployment via Rancher Desktop.
LIMITATIONS/ ASSUMPTIONS BELOW

## **Current MVP Limitations**

**⚠️ IMPORTANT: How to Retrieve Results from SAS Jobs**

- **All results you wish to retrieve _must_ be written to a specific table (dataset) in a specific library (e.g., `work_means` in the `work` library) _within your SAS code_.**
- **The API does _not_ return results from `PROC PRINT`, ODS OUTPUT, or SAS listing/log output.**
- **Only datasets (tables) created by your SAS code and fetched using the `/table` endpoint will be returned as results.**
- **Do _not_ change the output table or library unless you also update your API call to match.**
- **This is by design for the current MVP and will be revisited in future releases.**

---

**Key Features:**
- Standardized API endpoints for SAS code execution, job management, and results retrieval
- Consistent response schemas and robust error mapping
- Ready for containerized, cloud-native deployment (Rancher Desktop / Kubernetes)
- OpenAPI/Swagger documentation for easy exploration and integration
- **Interactive React-based Front-end:** Provides an interactive web UI for submitting SAS code and visualizing job status and results

---

## Tools & Functionality

| Functionality           | Endpoint   | What It Does                                         | Status                |
|------------------------|------------|------------------------------------------------------|-----------------------|
| **Run SAS Code**       | `/run`     | Submit SAS code for execution and get a job ID        | ✅ Ready              |
| **Check Job Status**   | `/status`  | Get the current state of a submitted SAS job          | ✅ Ready              |
| **Fetch Results**      | `/results` | Retrieve logs, listings, and output data              | ✅ Ready              |
| **Cancel a Job**       | `/cancel`  | Stop a SAS job that is currently executing            | ✅ Ready              |
| **Health Check**       | `/health`  | Confirm the MCP server is running                     | ✅ Ready              |
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

## Deployment

**Recommended:**  
- Rancher Desktop (Kubernetes) for local development and cloud simulation

**Quickstart:**
```sh
# Build Docker image
docker build -t mcp-sasviya-api:latest .

# Deploy to Kubernetes (Rancher Desktop)
kubectl apply -f deploy.yaml
kubectl apply -f service.yaml

# Access API docs
open http://localhost:30080/docs
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
