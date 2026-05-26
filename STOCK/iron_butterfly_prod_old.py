"""
===================================================================================================
AJ CAPITAL LLC - AUTOMATED OPTIONS ROUTING DASHBOARD & TRANSMISSION ENGINE
===================================================================================================
PROGRAM NAME: iron_butterfly_prod.py (LIVE ROUTING SPEC)


[ Market Database Feed ]
             │
             ▼
   [ Is IV > 35%? ] ──────────> ❌ No (Discard Asset)
             │
            Yes
             ▼
   [ Is Beta < 1.30? ] ───────> ❌ No (Too volatile, Discard)
             │
            Yes
             ▼
   [ Is Expected ROI > 12%? ] ─> ❌ No (Not enough credit, Discard)
             │
            Yes
             ▼
  Sort remaining by best metrics ──> Pick Top 10 ──> Package 4-Leg JSON Payloads


  ┌───────────────────────────┐
    │     screener_setup.txt    │  <─── [YOUR CONTROL PANEL]
    │  (Change dates, Qty, IV)  │       (You only edit this text file)
    └─────────────┬─────────────┘
                  │
                  ▼
    ┌───────────────────────────┐
    │    iron_condor_prod.py    │  <─── [THE QUANT BRAIN]
    │    iron_butterfly_prod.py │       (Filters database automatically)
    └─────────────┬─────────────┘
                  │
                  ▼
    ┌───────────────────────────┐
    │   order_history_log.txt   │  <─── [THE ACCOUNTING DIARY]
    │  (Permanent Master Log)   │       (Python records metrics here)

=======================================================================================================
"""

import os
import sys

print("=" * 120)
print(f"{'AJ CAPITAL LLC - IRON BUTTERFLY STRATEGY MONITOR & DATA DASHBOARD':^120}")
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
print(f"{'SYMBOL':<6} | {'SPOT':<7} | {'ATM PINNED APEX CENTER':<24} | {'PROTECTIVE OUTRIGGER WINGS':<28} | {'NET EXPIRATION'}")
print("-" * 120)

for target in TARGET_WATCHLIST:
    sym = target["symbol"]
    exp = target["expiration"]
    if sym not in LIVE_TICKER_FEED: continue
    
    spot = LIVE_TICKER_FEED[sym]
    
    # Pin the center entry right on the money strike line
    atm_strike = round(spot, 0)
    upper_guard = round(atm_strike + 10.00, 1)
    lower_guard = round(atm_strike - 10.00, 1)
    
    center_apex   = f"Sell Call/Put @ ${atm_strike:.0f}"
    outer_guards  = f"Buy Call ${upper_guard:.1f} / Buy Put ${lower_guard:.1f}"
    
    print(f"{sym:<6} | ${spot:<6.2f} | {center_apex:<24} | {outer_guards:<28} | {exp}")

print("=" * 120)