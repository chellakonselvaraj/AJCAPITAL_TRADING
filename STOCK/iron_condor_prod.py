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

def load_iron_condor_symbols(file_path="iron_condor_levels.txt"):
    """Reads your simple list of symbols and automatically formats index roots for dxFeed."""
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

def auto_calculate_wings(live_price):
    """Dynamically scales the wing distance out from the stock price."""
    if live_price > 500:
        return Decimal("15.00")
    elif live_price > 200:
        return Decimal("10.00")
    else:
        return Decimal("5.00")

async def continuous_iron_condor_tracker():
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    session = Session(client_secret, refresh_token)
    env_mode = "PRODUCTION"
    live_marks = {}

    try:
        async with DXLinkStreamer(session) as streamer:
            while True:
                watchlist = load_iron_condor_symbols()
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

                os.system('clear' if os.name == 'posix' else 'cls')
                
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f" {BOLD_WHITE}               AJ CAPITAL LLC - IRON CONDOR STRATEGY MONITOR & DATA DASHBOARD [{env_mode}]{RESET}")
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f"{BOLD_WHITE}{'SYMBOL':<6} | {'SPOT':<7} | {'CALL WING (Short / Long)':<25} | {'PUT WING (Short / Long)':<33} | {'NET EXPIRATION'}{RESET}")
                print(f"{BOLD_WHITE}------------------------------------------------------------------------------------------------------------------------{RESET}")
                
                for sym in watchlist:
                    underlying_price = live_marks.get(sym, Decimal("0.00"))
                    display_sym = sym.lstrip('.')
                    
                    if underlying_price > 0:
                        underlying_str = f"${underlying_price:,.2f}"
                        width = auto_calculate_wings(underlying_price)
                        base_price = underlying_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                        
                        p_short = base_price - width
                        p_long = p_short - Decimal("5.00")
                        c_short = base_price + width
                        c_long = c_short + Decimal("5.00")
                        
                        call_wing_str = f"Sell ${c_short:<5,.1f} / Buy ${c_long:<5,.1f}"
                        put_wing_str = f"Sell ${p_short:<5,.1f} / Buy ${p_long:<5,.1f}"
                        status_date = "2026-05-22"
                    else:
                        underlying_str = "Fetching..."
                        call_wing_str = f"Searching market..."
                        put_wing_str = f"Calculating wings..."
                        status_date = "2026-05-22"
                
                    print(f"{CYAN_TEXT}{display_sym:<6}{RESET} | {underlying_str:<7} | {call_wing_str:<25} | {put_wing_str:<33} | {status_date}")
                    print()
                    
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                await asyncio.sleep(10)
                
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n\n{BOLD_WHITE}[-] Iron Condor dashboard closed cleanly.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(continuous_iron_condor_tracker())
    except KeyboardInterrupt:
        pass