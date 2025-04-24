import requests
import time

BASE = "http://localhost:8000/api"

# Step 1: Run code
run_resp = requests.post(f"{BASE}/run", json={"code": "data work.results; x=1+2; output; run;"})
assert run_resp.status_code == 200, f"Run failed: {run_resp.text}"
run_data = run_resp.json()
session_id = run_data["session_id"]
job_id = run_data["job_id"]
assert session_id and job_id, f"Missing session_id/job_id: {run_data}"
print(f"Run: session_id={session_id}, job_id={job_id}")

# Step 2: Poll status until not running
for _ in range(10):
    status_resp = requests.get(f"{BASE}/status", params={"job_id": job_id, "session_id": session_id})
    assert status_resp.status_code == 200, f"Status failed: {status_resp.text}"
    status_data = status_resp.json()
    print(f"Status: {status_data}")
    if status_data["state"] != "running":
        break
    time.sleep(1)
else:
    raise RuntimeError("Job did not finish in time")

# Step 3: Get results
results_resp = requests.get(f"{BASE}/results", params={"job_id": job_id, "session_id": session_id})
assert results_resp.status_code == 200, f"Results failed: {results_resp.text}"
results_data = results_resp.json()
print(f"Results: {results_data}")

# Step 4: Get table
# Table should exist if SAS code ran successfully
table_resp = requests.get(f"{BASE}/table", params={"session_id": session_id, "library": "work", "table_name": "results"})
assert table_resp.status_code == 200, f"Table failed: {table_resp.text}"
table_data = table_resp.json()
print(f"Table: {table_data}")

print("Multi-step session test passed.")
