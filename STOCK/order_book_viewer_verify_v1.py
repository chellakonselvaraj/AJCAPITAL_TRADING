import os
import asyncio
import re
from tastytrade import Session, Account

async def main():
    # 1. Pull credentials from profile
    os.environ["TT_SECRET"] = os.environ.get('TASTY_CLIENT_SECRET', '')
    os.environ["TT_REFRESH"] = os.environ.get('TASTY_REFRESH_TOKEN', '')
    
    if not os.environ["TT_SECRET"] or not os.environ["TT_REFRESH"]:
        print("Error: Missing credentials inside your ~/.zshrc profile.")
        return

    session = Session()
    accounts = await Account.get(session)
    if not accounts:
        print("Error: No account profiles found.")
        return
    account = accounts[0]
    
    print("Connected to Live Account Profile [MASKED]")
    print("LOG: Extracting Raw Tickets with Tight 25-Character Single-Line Reason Boundaries...\n")
    
    raw_orders = await account.get_live_orders(session)
    
    if not raw_orders:
        print("No orders returned from the server.")
        return

    # Helper function to extract parameters from option tickers dynamically
    def parse_option_string(symbol_str):
        parts = symbol_str.split()
        if len(parts) < 2:
            return parts[0], "--", "--", "--"
            
        root_symbol = parts[0]
        option_part = parts[1]
        
        match = re.match(r'(\d{6})([CP])(\d{8})', option_part)
        if match:
            date_raw, cp_char, strike_raw = match.groups()
            try:
                formatted_date = f"20{date_raw[0:2]}-{date_raw[2:4]}-{date_raw[4:6]}"
            except Exception:
                formatted_date = date_raw
                
            cp_label = "CALL" if cp_char == 'C' else "PUT"
            strike_val = float(strike_raw) / 10000.0
            formatted_strike = f"${strike_val:.2f}"
            
            return root_symbol, formatted_date, formatted_strike, cp_label
            
        return root_symbol, "--", "--", "--"

    # 2. Flatten data and extract server rejection messages with truncation limits
    parsed_rows = []
    for order in raw_orders:
        order_id = str(order.id)
        status = str(order.status).split('.')[-1].upper() if order.status else "UNKNOWN"
        order_price = f"${float(order.price):.2f}" if order.price else "$0.00"
        
        reason_str = "--"
        if status in ["CANCELLED", "REJECTED"]:
            raw_msg = getattr(order, 'reject_reason', None) or getattr(order, 'cancellation_reason', None) or getattr(order, 'details', None) or "TIF Expired / Cleaned Out"
            raw_msg = str(raw_msg).strip()
            
            # --- PATCH: Strict 25-Character Truncation Control ---
            if len(raw_msg) > 25:
                reason_str = f"{raw_msg[:22]}..."
            else:
                reason_str = raw_msg

        for idx, leg in enumerate(order.legs):
            raw_symbol = getattr(leg, 'symbol', None) or getattr(leg, 'instrument_symbol', "--")
            action = getattr(leg, 'action', "--")
            
            root, expiry_date, strike_amt, cp_type = parse_option_string(raw_symbol)
            
            parsed_rows.append({
                'order_id': order_id if idx == 0 else "",
                'status': status if idx == 0 else "",
                'order_price': order_price if idx == 0 else "",
                'symbol': root,
                'expiry_date': expiry_date,
                'strike_amt': strike_amt,
                'cp_type': cp_type,
                'action': action,
                'reason': reason_str if idx == 0 else ""
            })

    # 3. DYNAMIC WIDTH CALCULATION ENGINE
    widths = {
        'order_id': max(len('Order ID'), max(len(r['order_id']) for r in parsed_rows)),
        'status': max(len('Server Status'), max(len(r['status']) for r in parsed_rows)),
        'order_price': max(len('Order Price'), max(len(r['order_price']) for r in parsed_rows)),
        'symbol': max(len('SYMBOL'), max(len(r['symbol']) for r in parsed_rows)),
        'expiry_date': max(len('EXPIRY DATE'), max(len(r['expiry_date']) for r in parsed_rows)),
        'strike_amt': max(len('CREDIT AMT'), max(len(r['strike_amt']) for r in parsed_rows)),
        'cp_type': max(len('CAL/PUT'), max(len(r['cp_type']) for r in parsed_rows)),
        'action': max(len('Leg Action'), max(len(r['action']) for r in parsed_rows)),
        'reason': max(len('REASON / CODE'), max(len(r['reason']) for r in parsed_rows))
    }

    total_line_len = sum(widths.values()) + (3 * (len(widths) - 1))

    # 4. Print the clean tabular matrix
    print("=" * total_line_len)
    print(f"{'Order ID':<{widths['order_id']}} | {'Server Status':<{widths['status']}} | {'Order Price':<{widths['order_price']}} | {'SYMBOL':<{widths['symbol']}} | {'EXPIRY DATE':<{widths['expiry_date']}} | {'CREDIT AMT':<{widths['strike_amt']}} | {'CAL/PUT':<{widths['cp_type']}} | {'Leg Action':<{widths['action']}} | {'REASON / CODE':<{widths['reason']}}")
    print("-" * total_line_len)

    current_id = ""
    for row in parsed_rows:
        if row['order_id'] and current_id and row['order_id'] != current_id:
            print("-" * total_line_len)
        
        if row['order_id']:
            current_id = row['order_id']

        print(f"{row['order_id']:<{widths['order_id']}} | {row['status']:<{widths['status']}} | {row['order_price']:<{widths['order_price']}} | {row['symbol']:<{widths['symbol']}} | {row['expiry_date']:<{widths['expiry_date']}} | {row['strike_amt']:<{widths['strike_amt']}} | {row['cp_type']:<{widths['cp_type']}} | {row['action']:<{widths['action']}} | {row['reason']:<{widths['reason']}}")

    print("=" * total_line_len)
    print(f"Total raw exchange ticket lines parsed: {len(raw_orders)} orders ({len(parsed_rows)} individual legs)")
    print("=" * total_line_len)

if __name__ == "__main__":
    asyncio.run(main())