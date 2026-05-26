import os
import asyncio
from tastytrade import Session
from tastytrade.instruments import Forex

async def test_connection():
    secret = os.environ.get("TASTY_CLIENT_SECRET")
    token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    print("[-] Initializing handshake with tastytrade authorization servers...")
    session = Session(secret, token)
    
    print("[-] Requesting 24-hour historical data candle array for EUR/USD...")
    try:
        instruments = await Forex.get_forex(session, ["EUR/USD"])
        if instruments:
            candles = await instruments[0].get_candles(session, period="1h")
            if candles:
                print(f"[+] SUCCESS! Server responded cleanly. Loaded {len(candles)} data points.")
                print(f"[+] Current Server Price: {candles[-1].close}")
                return
        print("[!] Server connected, but returned EMPTY historical data arrays.")
    except Exception as e:
        print(f"[X] Connection Error: {e}")

asyncio.run(test_connection())