import requests, json, os, base64

# --- Configuration ---
client_id = "api.client"
client_secret = "api.secret"
with open("access_server.txt", "r") as f:
    baseURL = f.read().strip()

# --- Step 1: Get Authorization Code ---
auth_url = f"{baseURL}/SASLogon/oauth/authorize?client_id={client_id}&response_type=code"
print(f"* Open this URL in an incognito browser and log in to generate your authorization code:\n{auth_url}")
auth_code = input("Enter the authorization code: ")

# --- Step 2: Exchange Auth Code for Tokens ---
# Encode client credentials in base64
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode("ascii")).decode("ascii")

# Build token URL and payload
token_url = f"{baseURL}/SASLogon/oauth/token#authorization_code"
payload = f"grant_type=authorization_code&code={auth_code}"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic " + encoded_credentials
}

response = requests.post(token_url, headers=headers, data=payload, verify=False)
if response.ok:
    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    print("\nAccess Token:", access_token)
    print("Refresh Token:", refresh_token)
    
    # Save tokens for reuse
    with open("access_token.txt", "w") as f:
        f.write(access_token)
    with open("refresh_token.txt", "w") as f:
        f.write(refresh_token)
    print("\nTokens stored as 'access_token.txt' and 'refresh_token.txt'.")
else:
    print("Token request failed:", response.text)

# --- (Optional) Example: Making an API Call ---
api_url = f"{baseURL}/reports/reports"  # Change endpoint as needed
api_headers = {"Authorization": f"Bearer {access_token}"}
api_response = requests.get(api_url, headers=api_headers, verify=False)
if api_response.ok:
    print("\nAPI Response:", json.dumps(api_response.json(), indent=4))
else:
    print("API call failed:", api_response.text)
