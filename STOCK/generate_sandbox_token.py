import requests
import json

url = "https://api.cert.tastyworks.com/sessions"
payload = {
    "login": "cselvarajsandbox",    # Replace with your sandbox login username
    "password": "SandBoxTasty!234" # Replace with your sandbox login password
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201 or response.status_code == 200:
        token = response.json()["data"]["session-token"]
        print("\n=================== FRESH SANDBOX TOKEN ===================")
        print(token)
        print("===========================================================\n")
    else:
        print(f"Failed to get token. Status: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")