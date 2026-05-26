import os
import subprocess
import requests

print("=" * 120)
print(f"{'AJ CAPITAL LLC - OAUTH2 PRODUCTION GATEWAY INITIALIZER':^120}")
print("=" * 120)

CLIENT_ID = os.environ.get("TASTY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TASTY_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("TASTY_REFRESH_TOKEN")

def fetch_oauth_access_token():
    token_url = "https://api.tastytrade.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_secret": CLIENT_SECRET
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "AJCapitalTrader/1.0"
    }
    print(" -> Transmitting secure OAuth2 grant token package...", end="", flush=True)
    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print(" ✅ AUTHORIZED")
            return response.json().get("access_token")
        else:
            print(f" ❌ REFUSED (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f" ❌ SECURITY HANDSHAKE TIMEOUT: {str(e)}")
        return None

LIVE_TOKEN = fetch_oauth_access_token()

if LIVE_TOKEN:
    print("=" * 120)
    print(" 🚀 Connection Validated. Injecting Token Directly Into DayTrader...")
    print("=" * 120)
    
    # 🎯 FORCE THE TOKEN INTO THE RELAY RUN:
    subprocess.run(["python3", "directional_daytrader.py", LIVE_TOKEN])
else:
    print(" ❌ System Halt: Handshake failed. Operational capital isolated safely.")
    print("=" * 120)