import os
import datetime
import asyncio
from tastytrade import Session, Account

async def main():
    # 1. Pull your existing custom variables from your ~/.zshrc profile
    custom_secret = os.environ.get('TASTY_CLIENT_SECRET')
    custom_refresh = os.environ.get('TASTY_REFRESH_TOKEN')

    if not custom_secret or not custom_refresh:
        print("Error: Missing credentials inside your ~/.zshrc profile.")
        return

    # 2. Hard-inject them using the EXACT environment names the SDK requires
    os.environ["TT_SECRET"] = custom_secret
    os.environ["TT_REFRESH"] = custom_refresh

    # 3. Initialize the session
    session = Session()

    # 4. Fetch connected accounts
    accounts = await Account.get(session)
    if not accounts:
        print("Error: No trading profiles linked to these token keys.")
        return
    account = accounts[0]

    print("Connected to Live Account Profile [MASKED]")
    print("-" * 115)
    print("Fetching COMPLETED History Logs & Bracket Target Matrices...")

    # 5. Fetch completed history using the verified endpoint (last 30 days)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    
    transactions = await account.get_history(session, start_date=start_date)

    # Print Upgraded Table Header matching your exact layout targets
    print(f"{'Date':<11} | {'ID / Order':<10} | {'Symbol':<24} | {'Action':<15} | {'Price':<9} | {'Target TP (80%)':<15} | {'Max SL (20%)':<13}")
    print("-" * 115)

    record_count = 0

    for tx in transactions:
        # Filter for actual trading activity safely
        if hasattr(tx, 'transaction_category') and tx.transaction_category != "Trade":
            continue
            
        record_count += 1
        
        # Parse basic parameters safely, forcing None values to readable fallback strings
        exec_date = tx.executed_at.strftime('%Y-%m-%d') if getattr(tx, 'executed_at', None) else "--"
        tx_id = str(tx.id)[:10] if getattr(tx, 'id', None) else "--"
        symbol = getattr(tx, 'symbol', None) or "--"
        action = getattr(tx, 'action', None) or "Trade"
        
        tp_val = "--"
        sl_val = "--"
        cost_basis = 0.0
        
        # Extract execution price cleanly from the history model variables
        if getattr(tx, 'price', None):
            cost_basis = float(tx.price)
        elif getattr(tx, 'price_effect', None):
            cost_basis = float(tx.price_effect)

        # Build clean string representations of values to dodge string formatting crashes
        price_str = f"${cost_basis:.2f}" if cost_basis > 0 else "--"

        if cost_basis > 0:
            # --- SHORT PREMIUM TRANSACTIONS (Selling options spreads or opening short futures layers) ---
            if action in ["Sell to Open", "Sell", "Sell to Close"]:
                tp_val = f"${(cost_basis * 0.20):.2f}"  # Profit target at 20% value remaining (80% profit)
                sl_val = f"${(cost_basis * 1.20):.2f}"  # Stop loss threshold if value expands by 20%
            
            # --- LONG DIRECTIONAL TRANSACTIONS (Buying shares or entering debit layers) ---
            elif action in ["Buy to Open", "Buy", "Buy to Close"]:
                tp_val = f"${(cost_basis * 1.80):.2f}"  # Profit target at 80% capital growth
                sl_val = f"${(cost_basis * 0.80):.2f}"  # Stop loss floor at 20% capital protection

        # All format targets are now absolute, guaranteed strings or structured numeric formats
        print(f"{exec_date:<11} | {tx_id:<10} | {symbol:<24} | {action:<15} | {price_str:<9} | {tp_val:<15} | {sl_val:<13}")

    print("-" * 115)
    print(f"Total verified history executions processed: {record_count}")
    print("=" * 115)

if __name__ == "__main__":
    asyncio.run(main())