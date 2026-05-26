import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session
from tastytrade.instruments import Equity
from tastytrade.order import NewOrder, OrderAction, OrderTimeInForce, OrderType

async def morning_live_equity_test():
    # 1. Pull the OAuth credentials securely from your environment variables
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        print("Please check that TASTY_CLIENT_SECRET and TASTY_REFRESH_TOKEN are defined in your .zshrc.")
        sys.exit(1)

    # 2. Establish connection
    print("Connecting to live tastytrade session via OAuth environment variables...")
    session = Session(client_secret, refresh_token)
    
    # 3. Retrieve your target trading account profile
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Account retrieval failed.")
        return
    account = accounts[0]
    print(f"Targeting Account Profile: {account.account_number}")

    # 4. Pull active equity parameters for BBAI
    print("Fetching equity data for BBAI...")
    bbai_stock = await Equity.get(session, "BBAI")
    
    # 5. Build individual share purchase leg (1 share, BUY_TO_OPEN)
    equity_leg = bbai_stock.build_leg(quantity=Decimal('1'), action=OrderAction.BUY_TO_OPEN)
    
    # 6. Define order framework limits
    # CRITICAL: A negative price tells the API engine this is a DEBIT transaction.
    # To buy 1 share at a maximum limit price of $1.50, we pass Decimal('-1.50').
    target_limit_price = Decimal('-1.50') 
    
    order_payload = NewOrder(
        time_in_force=OrderTimeInForce.DAY,
        order_type=OrderType.LIMIT,
        price=target_limit_price,
        legs=[equity_leg]
    )
    
    # 7. Route live order execution parameters
    print(f"Submitting LIVE limit order to buy 1 share of BBAI at absolute limit of $1.50 debit...")
    live_response = await account.place_order(session, order_payload, dry_run=False)
    
    # 8. Output server verification data
    print("\n--- LIVE ORDER SUBMISSION COMPLETE ---")
    print(f"Order Tracking ID: {live_response.order.id}")
    print(f"Current Order Status: {live_response.order.status}")
    
    if live_response.warnings:
        print(f"System Warnings: {live_response.warnings}")

if __name__ == "__main__":
    asyncio.run(morning_live_equity_test())