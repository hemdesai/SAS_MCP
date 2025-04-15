import os

def get_access_token():
    token_path = os.getenv("SAS_ACCESS_TOKEN_FILE", "access_token.txt")
    with open(token_path, "r") as f:
        return f.read().strip()

def get_sas_server_url():
    server_path = os.getenv("SAS_SERVER_FILE", "access_server.txt")
    with open(server_path, "r") as f:
        return f.read().strip()
