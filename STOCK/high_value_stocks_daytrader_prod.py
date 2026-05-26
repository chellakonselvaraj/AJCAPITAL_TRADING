import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session
from tastytrade.instruments import Equity

# --- SOLID MONOCHROME TERMINAL STYLES ---
RESET = "\033[0m"
BOLD_WHITE = "\033[1;37m"
CYAN_TEXT = "\033[1;36m"
BRIGHT_GREEN = "\033[1;92m"

ALERT_TEXT = ">>> Waiting for position entry fill..."

def load_stock_zones(file_path="stock_support_levels.txt"):
    """Dynamically parses stock levels from the local text configuration file."""
    watchlist = []
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("# symbol, planned_entry, target_zone, stop_loss\n")
        return watchlist

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parts = line.split(",")
                watchlist.append({
                    "symbol": parts[0].strip().upper(),
                    "entry": Decimal(parts[1].strip()),
                    "target": Decimal(parts[2].strip()),
                    "stop": Decimal(parts[3].strip())
                })
            except Exception:
                continue
    return watchlist

async def continuous_stock_tracker():
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
    
    env_mode = "SANDBOX" if "sandbox" in str(session).lower() else "PRODUCTION"

    # 2. Begin Active Engine Tracking Loop
    try:
        while True:
            watchlist = load_stock_zones()
            
            # Pull active positions to extract live marks and active flags
            positions = await account.get_positions(session)
            live_marks = {p.symbol.upper(): Decimal(str(p.close_price)) for p in positions if p.symbol and p.close_price is not None}
            active_positions = {p.symbol.upper() for p in positions if p.quantity and p.quantity > 0}
            
            # Clear terminal screen dynamically for a clean dashboard appearance
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 150)
            print(f" {BOLD_WHITE}HIGH-VALUE INTRADAY STOCKS TRACKER - [{env_mode}]  (Looping Refresh: 10s){RESET}")
            print(" Press [Ctrl + C] to safely shut down the tracker window.")
            print("=" * 150)
            print(f"{BOLD_WHITE}{'Ticker':<8} | {'Stock Price':<12} | {'Trade Direction':<16} | {'Planned Entry':<13} | {'Take Profit':<13} | {'Stop Loss':<11} | {'Zone Target Progress Bar & %'}{RESET}")
            print("-" * 150)
            
            for plan in watchlist:
                sym = plan["symbol"]
                entry = plan["entry"]
                target = plan["target"]
                stop_loss = plan["stop"]
                
                # Fetch mark price from open positions, or default to checking an underlying lookup path
                market_price = live_marks.get(sym, Decimal("0.00"))
                
                if market_price == 0:
                    try:
                        await Equity.get_equity(session, sym)
                        market_price = entry  # Fallback baseline during tracking wait states
                    except Exception:
                        pass
                
                market_price_str = f"${market_price:,.2f}" if market_price > 0 else "Fetching..."
                
                is_long = target > entry
                direction_str = "BULLISH LONG" if is_long else "BEARISH SHORT"
                total_width = abs(target - entry)
                
                is_filled = sym in active_positions
                
                if is_filled and market_price > 0:
                    distance = (market_price - entry) if is_long else (entry - market_price)
                    progress_pct = (distance / total_width) * 100
                    progress_pct = max(Decimal('0'), min(Decimal('100'), progress_pct))
                    
                    bar_length = 20
                    filled = int((progress_pct / 100) * bar_length)
                    bar_display = "#" * filled + "-" * (bar_length - filled)
                    progress_string = f"[{bar_display}] {BRIGHT_GREEN}{progress_pct:.1f}%{RESET}"
                else:
                    progress_string = ALERT_TEXT
                
                # Extended output grid mapping all three of your trading parameters explicitly
                print(f"{CYAN_TEXT}{sym:<8}{RESET} | {market_price_str:<12} | {direction_str:<16} | ${entry:<12,.2f} | ${target:<11,.2f} | ${stop_loss:<10,.2f} | {progress_string}")
                print()
                
            print("=" * 150)
            await asyncio.sleep(10)
            
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n\n{BOLD_WHITE}[-] Continuous stock dashboard closed out cleanly. Returning to terminal control.{RESET}\n")

if __name__ == "__main__":
    try:
        asyncio.run(continuous_stock_tracker())
    except KeyboardInterrupt:
        pass