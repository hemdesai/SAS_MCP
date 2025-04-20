import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv
import os, sys, json, time, requests

load_dotenv()
with open("access_server.txt", "r") as f:
    SAS_SERVER = f.read().strip()
with open("access_token.txt", "r") as f:
    SAS_ACCESS_TOKEN = f.read().strip()
TOKEN_VALIDITY_SECONDS = int(os.getenv("TOKEN_VALIDITY_SECONDS", 21600))
# Remind at 5.5 hours (19800 seconds)
TOKEN_RENEW_THRESHOLD = TOKEN_VALIDITY_SECONDS - 1800
token_start = time.time()

class SASService:
    def __init__(self, server, token):
        self.server = server
        self.token = token

    def _headers(self):
        return {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    
    def test_connection(self):
        url = self.server + "/folders/folders/@myFolder"
        try:
            r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
            if r.status_code == 200:
                return {"status_code": r.status_code, "message": "Connection successful", "data": r.json()}
            return {"status_code": r.status_code, "message": "Connection failed", "data": r.text}
        except Exception as e:
            return {"error": str(e)}
        
    def get_compute_context_uuid(self, context_name):
        url = self.server + f"/compute/contexts?filter=eq(name,'{context_name}')"
        try:
            r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
            if r.status_code == 200:
                data = r.json()
                return data['items'][0]['id'] if data.get("items") else None
            return None
        except Exception:
            return None
        
    def create_session(self, context_name="SAS Studio compute context"):
        ctx_uuid = self.get_compute_context_uuid(context_name)
        if not ctx_uuid: return None
        url = self.server + f"/compute/contexts/{ctx_uuid}/sessions"
        payload = {
            "version": 1,
            "name": "MCP",
            "description": "MCP session",
            "attributes": {},
            "environment": {"options": ["memsize=4g", "fullstimer"]}
        }
        try:
            r = requests.post(url, headers=self._headers(), json=payload, verify=False)
            return r.json().get("id") if r.status_code == 201 else None
        except Exception:
            return None
        
    def submit_code(self, session_id, sas_code):
        url = self.server + f"/compute/sessions/{session_id}/jobs"
        payload = {
            "version": 1,
            "name": "mcp",
            "description": "Submitting code from MCP",
            "code": sas_code,
            "attributes": {"resetLogLineNumbers": True}
        }
        try:
            r = requests.post(url, headers=self._headers(), json=payload, verify=False)
            return r.json().get("id") if r.status_code == 201 else None
        except Exception:
            return None
        
    def check_job_status(self, session_id, job_id):
        url = self.server + f"/compute/sessions/{session_id}/jobs/{job_id}/state"
        try:
            while True:
                r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
                if r.status_code == 200:
                    state = r.text.strip()
                    if state in ["pending", "running"]:
                        time.sleep(5)
                        continue
                    return state
                return None
        except Exception:
            return None
        
    def get_results(self, session_id, job_id, library="work", table="results", result_types=["log", "results", "data"]):
        results = {}
        if "log" in result_types:
            url = self.server + f"/compute/sessions/{session_id}/jobs/{job_id}/log?limit=100000"
            try:
                r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
                if r.status_code == 200: results["log"] = r.json().get("items")
            except Exception: pass
        if "results" in result_types:
            url = self.server + f"/compute/sessions/{session_id}/jobs/{job_id}/results?limit=100000"
            try:
                r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
                if r.status_code == 200: results["results"] = r.json().get("items")
            except Exception: pass
        if "data" in result_types:
            url = self.server + f"/compute/sessions/{session_id}/data/{library.upper()}/{table.upper()}/rows?limit=100000"
            try:
                r = requests.get(url, headers={"Authorization": "Bearer " + self.token}, verify=False)
                if r.status_code == 200: results["data"] = r.json().get("items")
            except Exception: pass
        return results

def check_token_expiry():
    if time.time() - token_start > TOKEN_RENEW_THRESHOLD:
        sys.stderr.write("Reminder: Access token is nearing expiry. Please renew it.\n")

def process_command(cmd):
    try:
        data = json.loads(cmd)
    except Exception:
        return {"error": "Invalid JSON"}
    action = data.get("action")
    sas = SASService(SAS_SERVER, SAS_ACCESS_TOKEN)
    if action == "test_connection":
        return sas.test_connection()
    elif action == "create_session":
        session_id = sas.create_session()
        return {"session_id": session_id} if session_id else {"error": "Could not create session"}
    elif action == "submit_code":
        sess = data.get("session_id")
        code = data.get("code")
        if not sess or not code:
            return {"error": "Missing session_id or code"}
        job = sas.submit_code(sess, code)
        return {"job_id": job} if job else {"error": "Code submission failed"}
    elif action == "check_job_status":
        sess = data.get("session_id")
        job = data.get("job_id")
        if not sess or not job:
            return {"error": "Missing session_id or job_id"}
        status = sas.check_job_status(sess, job)
        return {"status": status} if status else {"error": "Could not retrieve job status"}
    elif action == "get_results":
        sess = data.get("session_id")
        job = data.get("job_id")
        library = data.get("library", "work")
        table = data.get("table", "results")
        if not sess or not job:
            return {"error": "Missing session_id or job_id"}
        return {"results": sas.get_results(sess, job, library, table)}
    return {"error": "Unknown action"}

def main():
    sys.stdout.write("MCP SAS Viya server running. Awaiting JSON commands...\n")
    sys.stdout.flush()
    while True:
        check_token_expiry()
        rlist, _, _ = select.select([sys.stdin], [], [], 1.0)
        if rlist:
            line = sys.stdin.readline().strip()
            if not line:
                continue
            resp = process_command(line)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        time.sleep(0.1)
        
if __name__=="__main__":
    main()
