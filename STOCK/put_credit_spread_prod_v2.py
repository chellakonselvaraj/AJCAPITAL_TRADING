import os
import sys
import asyncio
from decimal import Decimal, ROUND_HALF_UP
from tastytrade import Session
from tastytrade.dxfeed import Quote
from tastytrade.streamer import DXLinkStreamer

# --- SOLID MONOCHROME TERMINAL STYLES ---
RESET = "\033[0m"
BOLD_WHITE = "\033[1;37m"
CYAN_TEXT = "\033[1;36m"

def load_watchlist_symbols(file_path="credit_spread.txt"):
    """Reads your dedicated credit spread symbols and formats index roots for dxFeed."""
    watchlist = []
    if not os.path.exists(file_path):
        return [".XSP", "SPY", "QQQ", "TSLA", "AAPL"]
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip().upper()
            if not line or line.startswith("#"):
                continue
            if line in ["XSP", "SPX", "RUT", "NDX"]:
                watchlist.append(f".{line}")
            else:
                watchlist.append(line)
    return watchlist

async def continuous_credit_spread_tracker():
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    session = Session(client_secret, refresh_token)
    env_mode = "PRODUCTION"
    
    # PERMANENT MEMORY CACHE - Outside the loop so data never wipes or flickers
    live_marks = {}

    try:
        async with DXLinkStreamer(session) as streamer:
            while True:
                watchlist = load_watchlist_symbols()
                await streamer.subscribe(Quote, watchlist)
                
                try:
                    for _ in range(len(watchlist) * 2):
                        item = await streamer.get_event(Quote)
                        if item and item.event_symbol:
                            sym = item.event_symbol.upper()
                            if item.bid_price and item.ask_price:
                                live_marks[sym] = (Decimal(str(item.bid_price)) + Decimal(str(item.ask_price))) / Decimal("2")
                            elif item.bid_price:
                                live_marks[sym] = Decimal(str(item.bid_price))
                except Exception:
                    pass

                # Clear terminal screen dynamically for a clean dashboard appearance
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # --- UNIFORM STARK BOLDED HEADER LINES ---
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f" {BOLD_WHITE}               AJ CAPITAL LLC - PUT CREDIT SPREAD MONITOR & DATA DASHBOARD [{env_mode}]{RESET}")
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f"{BOLD_WHITE}{'SYMBOL':<6} | {'SPOT':<7} | {'SHORT PUT TARGET STRIKE':<25} | {'LONG PROTECTIVE PUT WING':<33} | {'NET EXPIRATION'}{RESET}")
                print(f"{BOLD_WHITE}------------------------------------------------------------------------------------------------------------------------{RESET}")
                
                for sym in watchlist:
                    underlying_price = live_marks.get(sym, Decimal("0.00"))
                    display_sym = sym.lstrip('.')
                    
                    if underlying_price > 0:
                        underlying_str = f"${underlying_price:,.2f}"
                        
                        # Round safely to the nearest whole dollar baseline
                        base_strike = underlying_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                        
                        # Build your clean vertical credit spread strikes ($5 wide structural width)
                        short_put = base_strike - Decimal("5.00")
                        long_put = short_put - Decimal("5.00")
                        
                        short_str = f"Sell Put @ ${short_put}"
                        long_str = f"Buy Put ${long_put:.1f}"
                        status_date = "2026-05-22"
                    else:
                        underlying_str = "Fetching..."
                        short_str = "Searching market..."
                        long_str = "Calculating wings..."
                        status_date = "2026-05-22"
                    
                    # Perfect Double-Spaced Visual Layout Match
                    print(f"{CYAN_TEXT}{display_sym:<6}{RESET} | {underlying_str:<7} | {short_str:<25} | {long_str:<33} | {status_date}")
                    print()
                    
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                await asyncio.sleep(10)
                
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n\n{BOLD_WHITE}[-] Credit Spread dashboard closed cleanly. Returning to terminal control.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(continuous_credit_spread_tracker())
    except KeyboardInterrupt:
        pass