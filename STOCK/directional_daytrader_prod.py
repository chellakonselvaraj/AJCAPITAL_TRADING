# =================================================================================================
# ENGINE DEMARCATION LINE - MARKS THE ABSOLUTE START OF THE EXECUTION RUN
#
#
#[ Read live_price vs support_levels.txt ]
#                                         │
#                 ┌───────────────────────┼───────────────────────┐
#                 ▼                       ▼                       ▼
#       [ Price <= Floor ]        [ Floor < Price < Ceiling ]  [ Price >= Ceiling ]
#                 │                       │                       │
#                 ▼                       ▼                       ▼
#         📈 BUY LONG SIGNAL        ⏳ NO TREND ZONE         📉 SELL SHORT SIGNAL
#     (Enter at the bottom)         (Hold / Wait)           (Enter at the top)
#
#
#
#[Your iMac Engine] ----(Sends Refresh Token)----> [Tastytrade Live Server]
#                                                           |
#[Your iMac Engine] <---(Gives 15-Min Trade Pass)-----------+
#        |
#        +---> Starts 'directional_daytrader.py' with 100% Authorized Clearance!
# =================================================================================================
#
#
#

import os
import sys
import json
from datetime import datetime

print("=" * 120)
print(f"{'AJ CAPITAL LLC - MANUAL TRADING DASHBOARD & LEVEL MONITOR':^120}")
print("=" * 120)

# =================================================================================================
# 🎯 AJ CAPITAL LLC - SECURE DYNAMIC ACCESS CONFIGURATION (ZERO HARDCODING)
# =================================================================================================
SECRET_API_KEY = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TASTY_API_KEY")
TARGET_ACCOUNT = os.environ.get("TASTY_ACCOUNT_ID")

if not SECRET_API_KEY or not TARGET_ACCOUNT:
    print(" ❌ SECURITY HALT: Essential credentials missing from environment memory.")
    print("    👉 Please ensure your profile is sourced or run via main_launcher.py.")
    sys.exit(1)
# =================================================================================================

PROFIT_TARGET_TRAIL = 2.00   
STOP_LOSS_TRAIL     = 1.00   

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

def load_technical_chart_bounds(filename="support_levels.txt"):
    levels = {}
    if not os.path.exists(filename): return levels
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "," in line:
                parts = line.split(",")
                levels[parts[0].strip()] = {
                    "floor": float(parts[1].strip()),
                    "pivot": float(parts[2].strip()),
                    "ceiling": float(parts[3].strip())
                }
    return levels

CONFIG, TARGET_WATCHLIST = load_screener_and_watchlist()
CHART_ZONES = load_technical_chart_bounds()

LIVE_TICKER_FEED = {
    "AMAT":  {"live_price": 212.40},
    "AMD":   {"live_price": 176.20},   
    "COST":  {"live_price": 784.50},
    "NVDA":  {"live_price": 931.80},   
    "TSLA":  {"live_price": 174.10},   
    "MSFT":  {"live_price": 414.20},
    "GOOGL": {"live_price": 172.50},   
    "GOOG":  {"live_price": 173.10},
    "NFLX":  {"live_price": 610.90}
}

print(f" ACCOUNT ACTIVE: {TARGET_ACCOUNT} | POSITION QTY DIST: {CONFIG['ORDER_QTY']}")
print("-" * 120)
print(f"{'SYMBOL':<8} | {'PRICE':<8} | {'ZONE ACTION':<25} | {'LEGS SETUP':<12} | {'PROFIT TARGET':<15} | {'STOP LOSS':<12} | {'EXPIRATION'}")
print("-" * 120)

for target in TARGET_WATCHLIST:
    sym = target["symbol"]
    exp = target["expiration"]
    if sym not in LIVE_TICKER_FEED or sym not in CHART_ZONES: continue
    
    live_price = LIVE_TICKER_FEED[sym]["live_price"]
    zones = CHART_ZONES[sym]
    
    if live_price <= zones["floor"]:
        action = "🚨 BUY / BULLISH ENTRY"
        legs = "Long Stock"
        profit_target = f"${round(live_price + PROFIT_TARGET_TRAIL, 2):.2f}"
        stop_loss = f"${round(live_price - STOP_LOSS_TRAIL, 2):.2f}"
    elif live_price >= zones["ceiling"]:
        action = "🔥 SELL / BEARISH ENTRY"
        legs = "Short Stock"
        profit_target = f"${round(live_price - PROFIT_TARGET_TRAIL, 2):.2f}"
        stop_loss = f"${round(live_price + STOP_LOSS_TRAIL, 2):.2f}"
    else:
        action = "⏳ HOLD (Inside Bounds)"
        legs = "None"
        profit_target = "N/A"
        stop_loss = "N/A"
        
    print(f"{sym:<8} | ${live_price:<7.2f} | {action:<25} | {legs:<12} | {profit_target:<15} | {stop_loss:<12} | {exp}")

print("=" * 120)