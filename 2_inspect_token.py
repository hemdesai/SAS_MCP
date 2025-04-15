# inspect_token.py

import base64
import json

# Load access token from file
with open(r"C:\code\SAS_MCP\access_token.txt", "r") as f:
    token = f.read().strip()

# Split token into header, payload, signature
parts = token.split('.')
if len(parts) != 3:
    raise ValueError("Invalid JWT token format")

# Decode payload
payload_b64 = parts[1] + '==='  # pad base64
payload_bytes = base64.urlsafe_b64decode(payload_b64)
payload = json.loads(payload_bytes)

# Print client_id and full payload
print("client_id:", payload.get("client_id"))
print(json.dumps(payload, indent=2))
print("Decoded payload:", payload)