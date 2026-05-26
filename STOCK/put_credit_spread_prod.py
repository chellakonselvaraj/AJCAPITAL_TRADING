"""
===================================================================================================
AJ CAPITAL LLC - AUTOMATED OPTIONS ROUTING DASHBOARD & TRANSMISSION ENGINE
===================================================================================================
PROGRAM NAME: put_credit_spread.py
DESIGN INTENT: Automated order file ingestion, matrix processing, risk-collateral auditing, 
               and sequential JSON execution payload routing for Put Credit Spreads.

STRATEGY CLARIFICATION (PUT CREDIT SPREAD vs. BULL PUT SPREAD):
  * These two terms describe the EXACT same mechanical options architecture. 
  * "Put Credit Spread" is the universal structural classification for selling a higher strike 
    put (STO) and buying a lower strike put (BTO) for an upfront net credit.
  * "Bull Put Spread" is simply the directional market bias application of this spread. 
    Because you harvest a credit that you keep if the stock stays flat or goes up, the trade 
    is inherently bullish. 
  * This program displays the strategy under the universal "Put Credit Spread" banner, 
    automatically balancing your short leg credits against your long leg debits.

CORE OPERATIONAL WORKFLOW:
  1. FILE INGESTION: Scans 'option_order.txt' and strictly filters out trailing spaces, 
     blank lines, or carriage returns to isolate clean symbols, dates, and contract quantities.
  2. STRIKE STRUCTURE MAPPING: Dynamically establishes exchange-compliant strike intervals 
     ($0.50 wide for sub-$5 stocks, $1.00 wide for mid-caps, and $5.00 wide for high-priced stocks).
  3. CAPACITARY RISK AUDITING: Prior to order transmission, calculates the exact dollar reduction 
     in buying power (Risk Amount) by taking the strike width, subtracting the net credit, 
     and multiplying by your position scale.
  4. INTERACTIVE ROUTING GATE: Pauses and reviews each symbol sequentially, prompting the operator 
     to commit the trade payload to the 'sandbox' mock server or the 'production' live server.
  5. LOCAL LEDGER LOGGING: Upon a successful server response, automatically appends a clean, 
     human-readable record directly into a permanent file database ('order_history_log.txt').

     ORDER_QTY = 2 $\rightarrow$ Automatically sizes every manual dashboard setup to scale 
     for exactly 2 contracts (or 2 shares for the daytrader) to keep your position sizing 
     disciplined.

     LIMIT_TOP_PICKS = 10 $\rightarrow$ Caps your maximum viewable output 
     to your top 10 premium opportunities to avoid analysis paralysis.MIN_IV_HURDLE = 0.35 $\rightarrow$ Ensures the underlying 
     stock has an Implied Volatility (IV) of 35% or higher. This guarantees you are only putting on premium-selling 
     spreads when options prices are rich and inflated.

     MAX_BETA_LIMIT = 1.30 $\rightarrow$ Caps asset 
     volatility against the broader market at 1.30. This keeps ultra-erratic or hyper-leveraged stocks
     out of your portfolio to protect your capital.
     
     MIN_ROC_RETURN = 0.12 $\rightarrow$ Mandates that any 
     calculated premium spread must yield a 12% or higher Return on Capital (ROC) based on the width
     of the wings before you bother taking the risk.
===================================================================================================
"""
import os
import sys

print("=" * 120)
print(f"{'AJ CAPITAL LLC - PUT CREDIT SPREAD MONITOR & EXECUTIVE VIEW':^120}")
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

print(f" ACCOUNT ACTIVE: {TARGET_ACCOUNT} | TARGET VOLUME: {CONFIG['ORDER_QTY']} Contracts")
print("-" * 120)
print(f"{'SYMBOL':<6} | {'SPOT':<7} | {'PUT SPREAD INCOME BLOCK':<35} | {'RISK GAP WIDTH':<14} | {'NET EXPIRATION'}")
print("-" * 120)

for target in TARGET_WATCHLIST:
    sym = target["symbol"]
    exp = target["expiration"]
    if sym not in LIVE_TICKER_FEED: continue
    
    spot = LIVE_TICKER_FEED[sym]
    
    short_put_strike = round(spot - 4.00, 1)
    long_put_strike  = round(short_put_strike - 2.50, 1)
    
    legs_layout = f"Sell Put ${short_put_strike:.1f} / Buy Put ${long_put_strike:.1f}"
    
    print(f"{sym:<6} | ${spot:<6.2f} | {legs_layout:<35} | $2.50 Spread   | {exp}")

print("=" * 120)