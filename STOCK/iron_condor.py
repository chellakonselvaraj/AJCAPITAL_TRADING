"""
===================================================================================================
AJ CAPITAL LLC - AUTOMATED OPTIONS ROUTING DASHBOARD & TRANSMISSION ENGINE
===================================================================================================
PROGRAM NAME: iron_condor.py (DYNAMIC SCREENER MODE)
DESCRIPTION: Reads a minimalist watchlist, dynamically generates out-of-the-money strikes
             for ANY stock symbol, and displays them by performance in an ultra-clean layout.
===================================================================================================
"""
import os
import sys
import asyncio
from decimal import Decimal, ROUND_HALF_UP
from tastytrade import Account, Session

# --- SOLID MONOCHROME TERMINAL STYLES ---
RESET = "\033[0m"
BOLD_WHITE = "\033[1;37m"
CYAN_TEXT = "\033[1;36m"
BRIGHT_GREEN = "\033[1;92m"

def load_iron_condor_symbols(file_path="iron_condor_levels.txt"):
    """Reads your simple list of symbols from the text file."""
    watchlist = []
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("XSP\nSPY\nQQQ\n")
        return ["XSP", "SPY", "QQQ"]

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip().upper()
            if not line or line.startswith("#"):
                continue
            watchlist.append(line)
    return watchlist

def auto_calculate_wings(live_price):
    """Dynamically scales the wing distance based on the stock price."""
    if live_price > 500:
        return Decimal("15.00")  # e.g., XSP, NFLX
    elif live_price > 200:
        return Decimal("10.00")  # e.g., MSFT, NVDA
    else:
        return Decimal("5.00")   # e.g., TSLA, AAPL, AMD

async def continuous_iron_condor_tracker():
    # 1. Authenticate Infrastructure Session
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    session = Session(client_secret, refresh_token)
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Account lookup failed.")
        return
    account = accounts[0]
    
    env_mode = "PRODUCTION"

    # 2. Begin Active Engine Tracking Loop
    try:
        while True:
            watchlist = load_iron_condor_symbols()
            
            # Pull active positions to extract current underlying spot prices
            positions = await account.get_positions(session)
            live_marks = {p.symbol.upper(): Decimal(str(p.close_price)) for p in positions if p.symbol and p.close_price is not None}
            
            # Clear terminal screen dynamically for a clean dashboard appearance
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 145)
            print(f" {BOLD_WHITE}               AJ CAPITAL LLC - AUTOMATED IRON CONDOR MONITOR [{env_mode}]{RESET}")
            print(" Press [Ctrl + C] to safely shut down the tracker window. (Looping Refresh: 10s)")
            print("=" * 145)
            print(f" ACCOUNT ACTIVE: 5WI58821 | TRADE ALLOC QTY: 2")
            print("-" * 145)
            print(f"{BOLD_WHITE}{'SYMBOL':<8} | {'SPOT':<9} | {'CALL WING (Short / Long)':<30} | {'PUT WING (Short / Long)':<29} | {'STATUS'}{RESET}")
            print("-" * 145)
            
            for sym in watchlist:
                # Fetch the live underlying market price
                underlying_price = live_marks.get(sym, Decimal("0.00"))
                
                if underlying_price > 0:
                    underlying_str = f"${underlying_price:,.2f}"
                    
                    # Determine dynamic width based on asset price tier
                    width = auto_calculate_wings(underlying_price)
                    
                    # Round baseline safely to whole strikes
                    base_price = underlying_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    
                    # Calculate Spreads Automatically
                    p_short = base_price - width
                    p_long = p_short - Decimal("5.00")
                    c_short = base_price + width
                    c_long = c_short + Decimal("5.00")
                    
                    # Format layouts
                    call_wing_str = f"Sell ${c_short:<6,.1f} / Buy ${c_long:<6,.1f}"
                    put_wing_str = f"Sell ${p_short:<6,.1f} / Buy ${p_long:<6,.1f}"
                    
                    if underlying_price <= p_short:
                        status_str = "\033[1;31mPUT SHORT BREACHED\033[0m"
                    elif underlying_price >= c_short:
                        status_str = "\033[1;31mCALL SHORT BREACHED\033[0m"
                    else:
                        status_str = f"{BRIGHT_GREEN}SAFE INSIDE ZONE{RESET}"
                else:
                    underlying_str = "Fetching..."
                    call_wing_str = f"Searching market..."
                    put_wing_str = f"Searching market..."
                    status_str = "Monitoring..."
                
                # Double-spaced automated layout
                print(f"{CYAN_TEXT}{sym:<8}{RESET} | {underlying_str:<9} | {call_wing_str:<30} | {put_wing_str:<29} | {status_str}")
                print()
                
            print("=" * 145)
            await asyncio.sleep(10)
            
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n\n{BOLD_WHITE}[-] Iron Condor dashboard closed out cleanly. Returning to terminal control.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(continuous_iron_condor_tracker())
    except KeyboardInterrupt:
        pass