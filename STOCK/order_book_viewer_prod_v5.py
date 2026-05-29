import os
import datetime
import asyncio
import re
from tastytrade import Session, Account

async def main():
    # 1. Pull credentials from profile
    os.environ["TT_SECRET"] = os.environ.get('TASTY_CLIENT_SECRET', '')
    os.environ["TT_REFRESH"] = os.environ.get('TASTY_REFRESH_TOKEN', '')

    session = Session()
    accounts = await Account.get(session)
    if not accounts:
        print("Error: No trading profiles linked to these token keys.")
        return
    account = accounts[0]

    print("Connected to Live Account Profile [MASKED]")
    print("LOG: Fetching LIVE Positions, Working Orders, Valuations & Real-Time P&L Matrix...")

    # 2. Gather live endpoints
    live_orders = await account.get_live_orders(session)
    live_positions = await account.get_positions(session)

    master_list = []
    today = datetime.date.today()

    # Helper function to parse YYMMDD safely
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

    # Helper function to shorten option strings
    def shorten_option_strike(full_symbol):
        parts = full_symbol.split()
        if len(parts) < 2:
            return full_symbol
        strike_part = parts[1]
        clean_strike = re.sub(r'0+$', '', strike_part)
        clean_strike = re.sub(r'([CP])0+', r'\1', clean_strike)
        return clean_strike

    # Group pending multi-leg orders by Order ID
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

    # Add consolidated pending orders
    for o_id, data in pending_groups.items():
        if data['price'] == 0.0 or not data['legs']:
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
            'price': abs(data['price']),
            'unit_price': 0.0,  # Pending orders don't have a floating market price filled yet
            'total_value': 0.0,
            'current_val': 0.0,
            'pnl': 0.0,
            'is_pending': True
        })

    # Process live open portfolio holdings
    for pos in live_positions:
        qty = float(pos.quantity) if hasattr(pos, 'quantity') else float(getattr(pos, 'net_quantity', 0))
        if qty == 0:
            continue
            
        symbol = pos.symbol if hasattr(pos, 'symbol') else getattr(pos, 'underlying_symbol', 'UNKNOWN')
        cost_basis = float(pos.average_open_price) if getattr(pos, 'average_open_price', None) else 0.0
        if cost_basis <= 0:
            continue

        close_price = float(getattr(pos, 'close_price', cost_basis))

        # Adjust multipliers dynamically based on asset metrics
        if symbol.startswith("/MES") or symbol.startswith("/MNQ"):
            multiplier = 1.0
            total_value = abs(qty * cost_basis)
            current_val = abs(qty * close_price)
        else:
            multiplier = 100.0 if len(symbol.split()) > 1 else 1.0
            total_value = abs(qty * cost_basis * multiplier)
            current_val = abs(qty * close_price * multiplier)
        
        if qty < 0:
            pnl = total_value - current_val
            pos_action = "Short Position"
        else:
            pnl = current_val - total_value
            pos_action = "Long Position"

        exp_str, dte_val = calculate_option_dte(symbol)

        master_list.append({
            'date': "--",
            'expiry': exp_str,
            'dte_val': dte_val,
            'symbol': symbol,
            'action': pos_action,
            'qty': str(int(qty)),
            'price': cost_basis,
            'unit_price': close_price,
            'total_value': total_value,
            'current_val': current_val,
            'pnl': pnl,
            'is_pending': False
        })

    # 3. Sort explicitly by DTE
    master_list = sorted(master_list, key=lambda x: x['dte_val'], reverse=False)

    # 4. DYNAMIC WIDTH CALCULATION ENGINE
    widths = {
        'date': len('Order Date'), 'expiry': len('Expiry'), 'dte': len('DTE'),
        'symbol': len('Symbol / Complex'), 'action': len('Action / Status'), 'qty': len('Qty'),
        'price': len('Unit Cost'), 'unit_price': len('Unit Price'), 
        'total_value': len('Total Cost/Credit'), 'current_val': len('Current Val'),
        'pnl': len('P&L (+/-)'), 'tp': len('Target TP'), 'sl': len('Max SL')
    }

    rows_to_print = []
    for item in master_list:
        price_str = f"${item['price']:.2f}"
        
        if item['is_pending']:
            unit_price_str = "--"
            cost_str = "--"
            val_str = "--"
            pnl_str = "--"
        else:
            unit_price_str = f"${item['unit_price']:.2f}"
            val_str = f"${item['current_val']:.2f}"
            suffix = " Cr" if "Short" in item['action'] else " Db"
            cost_str = f"${item['total_value']:.2f}{suffix}"
            pnl_str = f"+${item['pnl']:.2f}" if item['pnl'] >= 0 else f"-${abs(item['pnl']):.2f}"

        tp_val = "--"
        sl_val = "--"
        cost_basis = item['price']
        symbol_upper = item['symbol'].upper()
        clean_action = item['action'].replace("[PENDING] ", "")

        # Target Bracket Routing Logic
        if symbol_upper.startswith("/MES") or symbol_upper.startswith("/MNQ"):
            if "Sell" in clean_action or "Short" in clean_action:
                tp_val = f"${(cost_basis * 0.90):.2f}"
                sl_val = f"${(cost_basis * 1.025):.2f}"
            else:
                tp_val = f"${(cost_basis * 1.10):.2f}"
                sl_val = f"${(cost_basis * 0.975):.2f}"
        else:
            tp_val = f"${(cost_basis * 1.80):.2f}"
            sl_val = f"${(cost_basis * 0.80):.2f}"

        dte_display = str(item['dte_val']) if item['dte_val'] != float('inf') else "--"

        row_data = {
            'date': item['date'], 'expiry': item['expiry'], 'dte': dte_display,
            'symbol': item['symbol'], 'action': item['action'], 'qty': item['qty'],
            'price_str': price_str, 'unit_price': unit_price_str, 'total_value': cost_str, 
            'current_val': val_str, 'pnl': pnl_str, 'tp': tp_val, 'sl': sl_val
        }
        rows_to_print.append(row_data)

        for key in widths:
            val_len = len(row_data[key if key != 'price' else 'price_str'])
            if val_len > widths[key]:
                widths[key] = val_len

    total_line_len = sum(widths.values()) + (3 * (len(widths) - 1))

    # 5. Print the upgraded matrix layout grid
    print("-" * total_line_len)
    print(f"{'Order Date':<{widths['date']}} | {'Expiry':<{widths['expiry']}} | {'DTE':<{widths['dte']}} | {'Symbol / Complex':<{widths['symbol']}} | {'Action / Status':<{widths['action']}} | {'Qty':<{widths['qty']}} | {'Unit Cost':<{widths['price']}} | {'Unit Price':<{widths['unit_price']}} | {'Total Cost/Credit':<{widths['total_value']}} | {'Current Val':<{widths['current_val']}} | {'P&L (+/-)':<{widths['pnl']}} | {'Target TP':<{widths['tp']}} | {'Max SL':<{widths['sl']}}")
    print("-" * total_line_len)

    for row in rows_to_print:
        print(f"{row['date']:<{widths['date']}} | {row['expiry']:<{widths['expiry']}} | {row['dte']:<{widths['dte']}} | {row['symbol']:<{widths['symbol']}} | {row['action']:<{widths['action']}} | {row['qty']:<{widths['qty']}} | {row['price_str']:<{widths['price']}} | {row['unit_price']:<{widths['unit_price']}} | {row['total_value']:<{widths['total_value']}} | {row['current_val']:<{widths['current_val']}} | {row['pnl']:<{widths['pnl']}} | {row['tp']:<{widths['tp']}} | {row['sl']:<{widths['sl']}}")

    print("-" * total_line_len)
    print(f"Total live active monitored entries: {len(master_list)}")
    print("=" * total_line_len)

if __name__ == "__main__":
    asyncio.run(main())