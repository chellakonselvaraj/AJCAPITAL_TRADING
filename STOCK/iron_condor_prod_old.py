import os
import sys

print("=" * 120)
print(f"{'AJ CAPITAL LLC - IRON CONDOR OPTIONS EXECUTIVE DASHBOARD':^120}")
print("=" * 120)

SECRET_API_KEY = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TASTY_API_KEY")
TARGET_ACCOUNT = os.environ.get("TASTY_ACCOUNT_ID")

if not SECRET_API_KEY or not TARGET_ACCOUNT:
    print(" ❌ SECURITY HALT: Essential credentials missing from environment memory.")
    print("    👉 Please ensure your profile is sourced or run via main_launcher.py.")
    sys.exit(1)

def load_screener_and_watchlist(filename="screener_setup.txt", watchlist_filename="watchlist.txt"):
    settings = {"ORDER_QTY": 1, "LIMIT_TOP_PICKS": 10}
    watchlist = []
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    if key == "ORDER_QTY": settings[key] = int(float(val))
                    elif "." in val: settings[key] = float(val)
                    else: settings[key] = int(val)
                    
    if os.path.exists(watchlist_filename):
        with open(watchlist_filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "," in line:
                    sym, exp_date = line.split(",", 1)
                    watchlist.append({"symbol": sym.strip(), "expiration": exp_date.strip()})
                else:
                    watchlist.append({"symbol": line, "expiration": None})
    return settings, watchlist

CONFIG, TARGET_WATCHLIST = load_screener_and_watchlist()

LIVE_TICKER_FEED = {
    "AMAT": 212.40, "AMD": 176.20, "COST": 784.50, "NVDA": 931.80, "TSLA": 174.10,
    "MSFT": 414.20, "GOOGL": 172.50, "GOOG": 173.10, "NFLX": 610.90
}

print(f" ACCOUNT ACTIVE: {TARGET_ACCOUNT} | TRADE ALLOC QTY: {CONFIG['ORDER_QTY']}")
print("-" * 120)
print(f"{'SYMBOL':<6} | {'SPOT':<7} | {'PUT WING (Long/Short)':<24} | {'CALL WING (Short/Long)':<24} | {'NET EXPIRATION'}")
print("-" * 120)

for target in TARGET_WATCHLIST:
    sym = target["symbol"]
    exp = target["expiration"]
    if sym not in LIVE_TICKER_FEED: continue
    
    spot = LIVE_TICKER_FEED[sym]
    
    # Precise premium harvesting offsets based on underlying spot value
    short_call = round(spot + 5.00, 1)
    long_call  = round(short_call + 5.00, 1)
    short_put  = round(spot - 5.00, 1)
    long_put   = round(short_put - 5.00, 1)
    
    put_wing  = f"${long_put:.1f} / ${short_put:.1f}"
    call_wing = f"${short_call:.1f} / ${long_call:.1f}"
    
    print(f"{sym:<6} | ${spot:<6.2f} | {put_wing:<24} | {call_wing:<24} | {exp}")

print("=" * 120)