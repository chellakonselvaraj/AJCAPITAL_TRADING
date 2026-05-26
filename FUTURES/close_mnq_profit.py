import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Account, Session
from tastytrade.instruments import Future
from tastytrade.order import NewOrder, OrderAction, OrderTimeInForce, OrderType

async def close_mnq_position():
    # 1. Load secure environment configurations
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing.")
        sys.exit(1)

    # 2. Establish live session connection
    print("Connecting to live tastytrade session...")
    session = Session(client_secret, refresh_token)
    
    # 3. Target your live profile
    accounts = await Account.get(session)
    if not accounts:
        print("Error: Account retrieval failed.")
        return
    account = accounts[0]
    print(f"Targeting Account Profile: {account.account_number}")

    # 4. Build the Future Instrument target for the June contract
    print("Building instrument parameters for /MNQM6...")
    # 'MNQ' is the root, 'M6' specifies the June 2026 expiration cycle
    mnq_future = await Future.get_future(session, product_code="MNQ", code="M6")
    
    # 5. Build individual buy leg to close the short position
    # Since you are short 1 contract, you BUY_TO_CLOSE 1 contract to lock in profit
    future_leg = mnq_future.build_leg(quantity=Decimal('1'), action=OrderAction.BUY_TO_CLOSE)
    
    # 6. Configure a Market Order to guarantee immediate execution at the current best price
    order_payload = NewOrder(
        time_in_force=OrderTimeInForce.DAY,
        order_type=OrderType.MARKET,
        legs=[future_leg]
    )
    
    # 7. Submit order to the exchange floor
    print("\n[CRITICAL] Submitting LIVE MARKET ORDER to BUY TO CLOSE 1 contract of /MNQM6...")
    live_response = await account.place_order(session, order_payload, dry_run=False)
    
    print("\n--- LIVE PROFIT LOCK COMPLETE ---")
    print(f"Order Tracking ID: {live_response.order.id}")
    print(f"Current Order Status: {live_response.order.status}")

if __name__ == "__main__":
    asyncio.run(close_mnq_position())