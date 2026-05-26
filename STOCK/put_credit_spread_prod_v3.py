import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from tastytrade import Session
from tastytrade.instruments import Equity
from tastytrade.dxfeed import Quote
from tastytrade.streamer import DXLinkStreamer

# --- SOLID MONOCHROME TERMINAL STYLES ---
RESET = "\033[0m"
BOLD_WHITE = "\033[1;37m"
CYAN_TEXT = "\033[1;36m"
BRIGHT_GREEN = "\033[1;92m"
BRIGHT_YELLOW = "\033[1;93m"

def load_stock_watchlist(file_path="credit_spread.txt"):
    """Reads your standard put credit spread watchlist targets."""
    if not os.path.exists(file_path):
        return ["SPY", "QQQ", "AAPL", "NVDA"]
    watchlist = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip().upper()
            if not line or line.startswith("#"):
                continue
            watchlist.append(line)
    return watchlist if watchlist else ["SPY", "QQQ", "AAPL", "NVDA"]

async def continuous_equity_tracker():
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    session = Session(client_secret, refresh_token)
    env_mode = "PRODUCTION"
    live_marks = {}
    fallback_marks = {}
    sr_levels = {}

    stocks = load_stock_watchlist()

    # --- AUTOMATED VERTICAL MATRIX ALGORITHMIC CALCULATOR ---
    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        for ticker in stocks:
            inst = await Equity.get_equity(session, ticker)
            if inst:
                candles = await inst.get_candles(session, period="1h", start_time=start_time)
                if candles:
                    highs = [Decimal(str(c.high)) for c in candles]
                    lows = [Decimal(str(c.low)) for c in candles]
                    closes = [Decimal(str(c.close)) for c in candles]
                    
                    sr_levels[ticker] = {
                        "resistance": max(highs),
                        "support": min(lows)
                    }
                    fallback_marks[ticker] = closes[-1]
    except Exception as e:
        print(f"Error calculating vertical matrix levels: {e}")
        await asyncio.sleep(4)

    try:
        async with DXLinkStreamer(session) as streamer:
            while True:
                stocks = load_stock_watchlist()
                await streamer.subscribe(Quote, stocks)
                
                try:
                    for _ in range(len(stocks) * 2):
                        item = await asyncio.wait_for(streamer.get_event(Quote), timeout=2.0)
                        if item and item.event_symbol:
                            tk = item.event_symbol.upper()
                            if item.bid_price and item.ask_price:
                                live_marks[tk] = (Decimal(str(item.bid_price)) + Decimal(str(item.ask_price))) / Decimal("2")
                            elif item.bid_price:
                                live_marks[tk] = Decimal(str(item.bid_price))
                except asyncio.TimeoutError:
                    pass

                os.system('clear' if os.name == 'posix' else 'cls')
                
                # --- UNIFORM STARK BOLDED HEADER LINES ---
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f" {BOLD_WHITE}               AJ CAPITAL LLC - AUTOMATED STANDARD PUT CREDIT RISK MONITOR [{env_mode}]{RESET}")
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                print(f"{BOLD_WHITE}{'TICKER':<8} | {'LIVE SPOT':<12} | {'AUTO SUPPORT':<14} | {'AUTO RESIST':<13} | {'STANDARD VERTICAL SPREAD ENGINE'}{RESET}")
                print(f"{BOLD_WHITE}------------------------------------------------------------------------------------------------------------------------{RESET}")
                
                for ticker in stocks:
                    underlying_price = live_marks.get(ticker, fallback_marks.get(ticker, Decimal("0.00")))
                    levels = sr_levels.get(ticker, {"support": Decimal("0.00"), "resistance": Decimal("0.00")})
                    
                    sup_str = f"${levels['support']:,.2f}" if levels['support'] > 0 else "Calculating..."
                    res_str = f"${levels['resistance']:,.2f}" if levels['resistance'] > 0 else "Calculating..."
                    
                    if underlying_price > 0 and levels['support'] > 0:
                        underlying_str = f"${underlying_price:,.2f}"
                        
                        range_width = levels['resistance'] - levels['support']
                        pct_from_floor = ((underlying_price - levels['support']) / range_width) * 100 if range_width > 0 else 50
                        
                        if pct_from_floor <= 25:
                            status_str = f"{BRIGHT_GREEN}SUPPORT FLOOR MET: RECENT LOW DEFENDED (CONFIRM DELTA / EXECUTE SPREAD){RESET}"
                        elif pct_from_floor >= 75:
                            status_str = f"{BRIGHT_YELLOW}RESISTANCE CEILING MET: DECREASED EDGE (PRESERVE CAPITAL / WAIT){RESET}"
                        else:
                            status_str = f"{BOLD_WHITE}MID-RANGE CONSOLIDATION: STABLE TREND (MONITORING LEVEL BOUNDARIES){RESET}"
                    else:
                        underlying_str = "Connecting..."
                        status_str = "Awaiting Session Open"
                    
                    print(f"{CYAN_TEXT}{ticker:<8}{RESET} | {underlying_str:<12} | {sup_str:<14} | {res_str:<13} | {status_str}")
                    print()
                    
                print(f"{BOLD_WHITE}========================================================================================================================{RESET}")
                await asyncio.sleep(10)
                
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n\n{BOLD_WHITE}[-] Standard put credit monitor closed cleanly.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(continuous_equity_tracker())
    except KeyboardInterrupt:
        pass