import os
import datetime
import asyncio
import re
from tastytrade import Session, Account

async def main():
    # 1. Pull credentials from profile
    custom_secret = os.environ.get('TASTY_CLIENT_SECRET')
    custom_refresh = os.environ.get('TASTY_REFRESH_TOKEN')

    if not custom_secret or not custom_refresh:
        print("Error: Missing credentials inside your ~/.zshrc profile.")
        return

    os.environ["TT_SECRET"] = custom_secret
    os.environ["TT_REFRESH"] = custom_refresh

    # 2. Initialize session and account
    session = Session()
    accounts = await Account.get(session)
    if not accounts:
        print("Error: No trading profiles linked to these token keys.")
        return
    account = accounts[0]

    print("Connected to Live Account Profile [MASKED]")
    print("LOG: Fetching LIVE Portfolio Positions, Active Pending Orders, Expirations & DTE Matrix...")

    # 3. Gather live endpoints
    live_orders = await account.get_live_orders(session)
    live_positions = await account.get_positions(session)

    master_list = []
    today = datetime.date.today()

    # Helper function to parse YYMMDD from Option Ticker Strings safely
    def calculate_option_dte(symbol_str):
        if not symbol_str or symbol_str == "--":
            return "--", float('inf')
        try:
            match = re.search(r'\d{6}', symbol_str)
            if match:
                date_raw = match.group(0)
                exp_date = datetime.datetime.strptime(date_raw, "%y%m%d").date()
                dte = (exp_date - today).days
                return exp_date.strftime('%Y-%m-%d'), dte
        except Exception:
            pass
        return "--", float('inf')

    # Helper function to shorten full option strings for clean display layout tracking
    def shorten_option_strike(full_symbol):
        parts = full_symbol.split()
        if len(parts) < 2:
            return full_symbol
        strike_part = parts[1]
        clean_strike = re.sub(r'0+$', '', strike_part)
        clean_strike = re.sub(r'([CP])0+', r'\1', clean_strike)
        return clean_strike

    # Group pending multi-leg orders by Order ID to eliminate screen clutter
    pending_groups = {}
    for order in live_orders:
        status_str = str(order.status).split('.')[-1].lower() if order.status else ""
        if status_str in ["filled", "cancelled", "rejected", "expired"]:
            continue
            
        order_id = str(order.id)
        if order_id not in pending_groups:
            pending_groups[order_id] = {
                'legs': [],
                'price': float(order.price) if order.price else 0.0,
                'action': "",
                'order_date': order.received_at.strftime('%Y-%m-%d') if order.received_at else "--"
            }
        
        for leg in order.legs:
            symbol = getattr(leg, 'symbol', None) or getattr(leg, 'instrument_symbol', "--")
            pending_groups[order_id]['legs'].append(symbol)
            if not pending_groups[order_id]['action']:
                pending_groups[order_id]['action'] = leg.action

    # Add consolidated pending orders with dynamic multi-strike labels
    for o_id, data in pending_groups.items():
        if data['price'] <= 0 or not data['legs']:
            continue

        unique_underlyings = set([sym.split()[0] for sym in data['legs'] if sym != "--"])
        base_ticker = list(unique_underlyings)[0] if unique_underlyings else "--"
        
        first_leg = data['legs'][0] if data['legs'] else "--"
        exp_str, dte_val = calculate_option_dte(first_leg)
        
        if len(data['legs']) > 1:
            shortened_legs = [shorten_option_strike(l) for l in data['legs'] if l != "--"]
            display_symbol = f"{base_ticker} ({', '.join(shortened_legs)})"
        else:
            display_symbol = data['legs'][0]
        
        master_list.append({
            'date': data['order_date'],
            'expiry': exp_str,
            'dte_val': dte_val,
            'symbol': display_symbol,
            'action': f"[PENDING] {data['action']}",
            'qty': "---",
            'price': data['price'],
            'is_pending': True
        })

    # Process live open portfolio holdings (AAPL, TSLA, NFLX, Hedges)
    for pos in live_positions:
        qty = float(pos.quantity) if hasattr(pos, 'quantity') else float(getattr(pos, 'net_quantity', 0))
        if qty == 0:
            continue
            
        symbol = pos.symbol if hasattr(pos, 'symbol') else getattr(pos, 'underlying_symbol', 'UNKNOWN')
        cost_basis = float(pos.average_open_price) if getattr(pos, 'average_open_price', None) else 0.0
        
        if cost_basis <= 0:
            continue

        pos_action = "Short Position" if qty < 0 else "Long Position"
        exp_str, dte_val = calculate_option_dte(symbol)

        master_list.append({
            'date': "--",
            'expiry': exp_str,
            'dte_val': dte_val,
            'symbol': symbol,
            'action': pos_action,
            'qty': str(int(qty)),
            'price': cost_basis,
            'is_pending': False
        })

    # 4. Sort explicitly by DTE
    master_list = sorted(master_list, key=lambda x: x['dte_val'], reverse=False)

    # 5. DYNAMIC WIDTH CALCULATION ENGINE
    widths = {
        'date': len('Order Date'),
        'expiry': len('Expiry'),
        'dte': len('DTE'),
        'symbol': len('Symbol / Complex'),
        'action': len('Action / Status'),
        'qty': len('Qty'),
        'price': len('Net Cost'),
        'tp': len('Target TP (80%)'),
        'sl': len('Max SL (20%)')
    }

    rows_to_print = []
    for item in master_list:
        price_str = f"${item['price']:.2f}"
        tp_val = "--"
        sl_val = "--"
        cost_basis = item['price']
        symbol_upper = item['symbol'].upper()

        clean_action = item['action'].replace("[PENDING] ", "")

        # --- SMART CALCULATION ROUTER BASED ON ASSET TYPE ---
        
        # A. Check if it is a pure Index Futures contract (/MES or /MNQ)
        if symbol_upper.startswith("/MES") or symbol_upper.startswith("/MNQ"):
            # For micro futures, typical intraday point scale rules apply instead of doubling the asset
            # TP at 10% cash value expansion, SL at 2.5% tight protective trailing risk
            if "Sell" in clean_action or "Short" in clean_action:
                tp_val = f"${(cost_basis * 0.90):.2f}"
                sl_val = f"${(cost_basis * 1.025):.2f}"
            else:
                tp_val = f"${(cost_basis * 1.10):.2f}"
                sl_val = f"${(cost_basis * 0.975):.2f}"

        # B. Check if it is an Options Spread or Premium Contract (indicated by parentheses or long strings)
        elif "(" in symbol_upper or len(symbol_upper.split()) > 1:
            # Short Premium targets capturing 80% value (Buy back at 20% remaining value)
            if "Sell" in clean_action or "Short" in clean_action:
                tp_val = f"${(cost_basis * 0.20):.2f}"
                sl_val = f"${(cost_basis * 1.20):.2f}"
            else:
                tp_val = f"${(cost_basis * 1.80):.2f}"
                sl_val = f"${(cost_basis * 0.80):.2f}"

        # C. Standard Directional Equity Share Rules (AAPL, TSLA, NFLX)
        else:
            if "Sell" in clean_action or "Short" in clean_action:
                tp_val = f"${(cost_basis * 0.20):.2f}"
                sl_val = f"${(cost_basis * 1.20):.2f}"
            elif "Buy" in clean_action or "Long" in clean_action:
                tp_val = f"${(cost_basis * 1.80):.2f}"
                sl_val = f"${(cost_basis * 0.80):.2f}"

        dte_display = str(item['dte_val']) if item['dte_val'] != float('inf') else "--"

        row_data = {
            'date': item['date'],
            'expiry': item['expiry'],
            'dte': dte_display,
            'symbol': item['symbol'],
            'action': item['action'],
            'qty': item['qty'],
            'price_str': price_str,
            'tp': tp_val,
            'sl': sl_val
        }
        rows_to_print.append(row_data)

        for key in widths:
            val_len = len(row_data[key if key != 'price' else 'price_str'])
            if val_len > widths[key]:
                widths[key] = val_len

    total_line_len = sum(widths.values()) + (3 * (len(widths) - 1))

    # Print dynamically configured calendar-priority layout table
    print("-" * total_line_len)
    print(f"{'Order Date':<{widths['date']}} | {'Expiry':<{widths['expiry']}} | {'DTE':<{widths['dte']}} | {'Symbol / Complex':<{widths['symbol']}} | {'Action / Status':<{widths['action']}} | {'Qty':<{widths['qty']}} | {'Net Cost':<{widths['price']}} | {'Target TP (80%)':<{widths['tp']}} | {'Max SL (20%)':<{widths['sl']}}")
    print("-" * total_line_len)

    for row in rows_to_print:
        print(f"{row['date']:<{widths['date']}} | {row['expiry']:<{widths['expiry']}} | {row['dte']:<{widths['dte']}} | {row['symbol']:<{widths['symbol']}} | {row['action']:<{widths['action']}} | {row['qty']:<{widths['qty']}} | {row['price_str']:<{widths['price']}} | {row['tp']:<{widths['tp']}} | {row['sl']:<{widths['sl']}}")

    print("-" * total_line_len)
    print(f"Total live active monitored entries: {len(master_list)}")
    print("=" * total_line_len)

if __name__ == "__main__":
    asyncio.run(main())