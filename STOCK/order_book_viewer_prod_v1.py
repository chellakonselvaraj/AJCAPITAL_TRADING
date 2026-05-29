import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session

async def view_production_orders():
    # 1. Load Environment OAuth
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    session = Session(client_secret, refresh_token)
    
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Live account retrieval failed.")
        return
    account = accounts[0]
    print(f"Connected to Live Account Profile: {account.account_number}")
    print("-" * 50)

    # 2. CACHE REAL OPEN POSITIONS WITH TRUE COST BASIS
    print("Caching true historical portfolio cost basis...")
    positions = await account.get_positions(session)
    
    # Map out the exact metrics tastytrade sees on your app screen
    # Store: { 'SYMBOL': (true_average_open_price, current_live_market_price, quantity_direction) }
    portfolio_map = {}
    for pos in positions:
        symbol = pos.symbol.upper() if pos.symbol else "N/A"
        
        # 'average_open_price' is your actual filled cost basis
        avg_open = getattr(pos, 'average_open_price', None)
        # 'last_price' or 'close_price' is the active market rate
        live_price = getattr(pos, 'last_price', None) or getattr(pos, 'close_price', None)
        # Quantity can be positive (long) or negative (short)
        qty = getattr(pos, 'quantity', Decimal('0'))
        
        if avg_open is not None and live_price is not None:
            portfolio_map[symbol] = {
                'avg_open': Decimal(str(avg_open)),
                'live_price': Decimal(str(live_price)),
                'qty': Decimal(str(qty))
            }

    # 3. Fetch Live Order Log
    print("Fetching live order book records...")
    live_orders = await account.get_live_orders(session)
    
    if not live_orders:
        print("No order records found.")
        return

    live_orders.sort(key=lambda x: str(x.updated_at) if x.updated_at else "")

    print(f"\nFound {len(live_orders)} records:")
    print(f"{'Date':<10} | {'Order ID':<12} | {'Symbol':<8} | {'Action':<15} | {'Real Bought':<11} | {'Current Prc':<11} | {'True P/L':<10}")
    print("-" * 120)

    last_processed_date = None

    for order in live_orders:
        order_date = "N/A"
        if order.updated_at:
            order_date = str(order.updated_at).split(" ")[0].split("T")[0]

        if last_processed_date is not None and order_date != last_processed_date:
            print("=" * 120)
        
        last_processed_date = order_date

        leg = order.legs[0] if order.legs else None
        symbol = leg.symbol.upper() if leg and leg.symbol else "N/A"
        action = leg.action if leg else "N/A"
        
        # Default layout views
        bought_price_str = "--"
        current_price_str = "--"
        pl_string = "--"
        
        # Check if this asset is a live active position in your account right now
        if symbol in portfolio_map:
            pos_data = portfolio_map[symbol]
            
            # Extract values from the true position map
            true_cost_basis = pos_data['avg_open']
            market_price = pos_data['live_price']
            position_qty = pos_data['qty'] # This preserves the native long/short direction
            
            bought_price_str = f"${true_cost_basis:,.2f}"
            current_price_str = f"${market_price:,.2f}"
            
            # --- FUTURES MULTIPLIER ENGINE ---
            multiplier = Decimal('1')
            if symbol.startswith("/MES"):
                multiplier = Decimal('5')
            elif symbol.startswith("/MNQ"):
                multiplier = Decimal('2')
            # ---------------------------------
            
            # Core mathematical calculation mapping directly to your account balances:
            # For short positions, position_qty is negative.
            # (Market Price - True Cost) * Negative Qty correctly yields profit when market drops!
            total_pl = (market_price - true_cost_basis) * position_qty * multiplier
            
            sign = "+" if total_pl >= 0 else ""
            pl_string = f"{sign}${total_pl:,.2f}"
        else:
            # Fallback for old/canceled logs not currently in your active inventory
            if order.price is not None:
                bought_price_str = f"${abs(order.price):,.2f}"

        print(f"{order_date:<10} | {order.id:<12} | {symbol:<8} | {action:<15} | {bought_price_str:<11} | {current_price_str:<11} | {pl_string:<10}")

if __name__ == "__main__":
    asyncio.run(view_production_orders())