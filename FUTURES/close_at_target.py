import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session
from tastytrade.instruments import Future
from tastytrade.order import NewOrder, OrderAction, OrderTimeInForce, OrderType

# ==============================================================================
# CONFIGURATION WINDOW (SAFELY LOCKED IN SIMULATION MODE)
# ==============================================================================
# DRY_RUN = True           True = SIMULATE targets safely. False = SEND LIVE ORDERS.
# DRY_RUN = False          Flip this to False to run ON the live routing wires.
# PROFIT_TARGET_PCT = 6.0  Your exact target threshold percentage. Run when reaches Profit Target 6% or higher.
# PROFIT_TARGET_PCT = 0.0  Set to 0.0 for testing the trigger logic without waiting for price movement.
# ==============================================================================
# ==============================================================================

DRY_RUN = True          # True = SIMULATE targets safely. False = SEND LIVE ORDERS.
PROFIT_TARGET_PCT = 6.0 # Your exact target threshold percentage. Run when reaches Profit Target 6% or higher.


async def automate_futures_profit_taking():
    # 1. Load Secure Environment Profiles
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing in this terminal session.")
        sys.exit(1)

    # 2. Establish Session Architecture
    session = Session(client_secret, refresh_token)
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Account lookup failed.")
        return
    account = accounts[0]
    
    env_mode = "SANDBOX" if "sandbox" in str(session).lower() else "PRODUCTION"
    
    print("=" * 90)
    print(f" FUTURES PROFIT TARGET AUTOMATOR - [{env_mode}]")
    print(f" SAFETY STATUS: {'[DRY RUN - SIMULATION MODE]' if DRY_RUN else '[LIVE ROUTING ACTIVATED]'}")
    print("=" * 90)

    # 3. Harvest Active Inventory
    positions = await account.get_positions(session)
    futures_positions = [p for p in positions if p.symbol and p.symbol.startswith("/")]
    
    if not futures_positions:
        print("\nNo active futures positions found to automate.")
        return

    print(f"\nScanning {len(futures_positions)} Positions for Profit Target Triggers ({PROFIT_TARGET_PCT}%):\n")

    # 4. Loop Through and Check Boundaries
    for pos in futures_positions:
        symbol = pos.symbol.upper()
        qty = Decimal(str(pos.quantity))
        avg_open = Decimal(str(pos.average_open_price))
        live_price = Decimal(str(pos.close_price)) if pos.close_price is not None else avg_open
        
        direction = "LONG" if qty > 0 else "SHORT"
        display_qty = abs(int(qty))
        
        # Calculate point gap threshold for a 6% move
        points_target_gap = avg_open * Decimal(str(PROFIT_TARGET_PCT / 100))
        
        # Derive target price rules based on position trade vectors
        if direction == "LONG":
            target_price = avg_open + points_target_gap
            progress_pct = ((live_price - avg_open) / points_target_gap) * 100
            trigger_hit = live_price >= target_price
        else:
            target_price = avg_open - points_target_gap
            progress_pct = ((avg_open - live_price) / points_target_gap) * 100
            trigger_hit = live_price <= target_price

        # Cap reporting metrics for visual neatness
        progress_pct = max(Decimal('0'), progress_pct)

        print(f"» {symbol} ({direction} x{display_qty})")
        print(f"  Entry: ${avg_open:,.2f}  |  Current: ${live_price:,.2f}")
        print(f"  6% Target Goal Price Level: ${target_price:,.2f}")
        print(f"  Target Run Progress: {progress_pct:.1f}% toward target")

        # 5. Execution Trigger Logic Rule Block
        if trigger_hit:
            print(f"  🚨 TARGET ACHIEVED for {symbol}! Initiating automated liquidating vector...")
            
            # Formulate closing instructions
            close_action = OrderAction.SELL_TO_CLOSE if direction == "LONG" else OrderAction.BUY_TO_CLOSE
            
            # Separate the root code (e.g., 'MNQ') from the specific month code (e.g., 'M6')
            clean_symbol = symbol.lstrip("/")  # Remove forward slash for SDK resolution
            product_code = "".join([c for c in clean_symbol if c.isalpha()])[:-2] # Extracts MNQ or MES
            contract_code = clean_symbol[len(product_code):] # Extracts M6
            
            try:
                # Fetch target instrument footprint mapping from tastytrade exchange floor
                future_instrument = await Future.get_future(session, product_code=product_code, code=contract_code)
                future_leg = future_instrument.build_leg(quantity=display_qty, action=close_action)
                
                # Construct aggressive Market Order to lock in value instantly
                order_payload = NewOrder(
                    time_in_force=OrderTimeInForce.DAY,
                    order_type=OrderType.MARKET,
                    legs=[future_leg]
                )
                
                if DRY_RUN:
                    print(f"  [SIMULATION] Would have routed a LIVE MARKET order to {close_action.name} {display_qty} contract(s) of {symbol}.")
                else:
                    print(f"  [EXECUTION] Transmitting LIVE order payload to tastytrade routers...")
                    response = await account.place_order(session, order_payload, dry_run=False)
                    print(f"  [SUCCESS] Order Sent! Status: {response.order.status} | Order ID: {response.order.id}")
            except Exception as e:
                print(f"  [ERROR] Failed to compile order mapping for {symbol}: {e}")
        else:
            print(f"  Horizontal holding pattern: Waiting for price action to bridge gaps.")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(automate_futures_profit_taking())