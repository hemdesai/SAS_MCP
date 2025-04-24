import os

def get_access_token():
    import os
    if not os.getenv("SAS_ACCESS_TOKEN"):
        token_path = os.getenv("SAS_ACCESS_TOKEN_FILE", "access_token.txt")
        with open(token_path, "r") as f:
            os.environ["SAS_ACCESS_TOKEN"] = f.read().strip()
    return os.getenv("SAS_ACCESS_TOKEN")

def get_sas_server_url():
    import os
    if not os.getenv("SAS_SERVER"):
        server_path = os.getenv("SAS_SERVER_FILE", "access_server.txt")
        with open(server_path, "r") as f:
            os.environ["SAS_SERVER"] = f.read().strip()
    return os.getenv("SAS_SERVER")
