import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session

async def monitor_futures_positions():
    # 1. Load secure OAuth environment keys
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing in this terminal session.")
        sys.exit(1)

    # 2. Establish live session connection
    session = Session(client_secret, refresh_token)
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Account lookup failed.")
        return
    account = accounts[0]
    
    # 3. Environment Tag Setup
    # Safely checks the text representation of the session object for sandbox flags
    env_mode = "SANDBOX" if "sandbox" in str(session).lower() else "PRODUCTION"
    
    print("=" * 80)
    print(f" LIVE FUTURES PORTFOLIO MONITOR - [{env_mode}] MODE")
    print("=" * 80)

    # 4. Fetch active portfolio contents
    positions = await account.get_positions(session)
    
    # ISOLATION FILTER: Capture ONLY futures instruments (prefixed with a forward slash)
    futures_positions = [p for p in positions if p.symbol and p.symbol.startswith("/")]
    
    if not futures_positions:
        print("\nNo active futures contracts found in your portfolio right now.")
        print("=" * 80)
        return

    print(f"\nFound {len(futures_positions)} Active Futures Positions:")
    print(f"{'Symbol':<10} | {'Direction':<10} | {'Qty':<4} | {'Avg Entry':<12} | {'Current Mark':<12} | {'True Cash P/L':<12}")
    print("-" * 80)

    # 5. Process calculations using native exchange multiplier contracts
    for pos in futures_positions:
        symbol = pos.symbol.upper()
        qty = Decimal(str(pos.quantity))
        avg_open = Decimal(str(pos.average_open_price))
        
        # CurrentPosition uses close_price as its core market mark valuation parameter
        live_price = Decimal(str(pos.close_price)) if pos.close_price is not None else avg_open
        
        # Determine long vs short trade flow dynamics
        direction = "LONG" if qty > 0 else "SHORT"
        display_qty = abs(int(qty))
        
        # --- NATIVE EXCHANGE CONTRACT MULTIPLIERS ---
        multiplier = Decimal('1')
        if symbol.startswith("/MES"):
            multiplier = Decimal('5')   # Micro S&P 500 -> $5 per full point
        elif symbol.startswith("/MNQ"):
            multiplier = Decimal('2')   # Micro Nasdaq-100 -> $2 per full point
        # ---------------------------------------------
        
        # Calculate raw point movement gap
        price_diff = live_price - avg_open
        if direction == "SHORT":
            price_diff = -price_diff  # Short vectors gain capital when prices decline
            
        # Extract direct multi-contract absolute cash return exposure
        cash_pl = price_diff * abs(qty) * multiplier
        
        # Define the trend sign first, then format the output strings
        sign = "+" if cash_pl >= 0 else ""
        
        avg_open_str = f"${avg_open:,.2f}"
        live_price_str = f"${live_price:,.2f}"
        cash_pl_str = f"{sign}${cash_pl:,.2f}"
        
        print(f"{symbol:<10} | {direction:<10} | {display_qty:<4} | {avg_open_str:<12} | {live_price_str:<12} | {cash_pl_str:<12}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(monitor_futures_positions())