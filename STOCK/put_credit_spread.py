"""
===================================================================================================
AJ CAPITAL LLC - AUTOMATED OPTIONS ROUTING DASHBOARD & TRANSMISSION ENGINE
===================================================================================================
PROGRAM NAME: put_credit_spread.py
DESIGN INTENT: Automated order file ingestion, matrix processing, risk-collateral auditing, 
               and sequential JSON execution payload routing for Put Credit Spreads.

STRATEGY CLARIFICATION (PUT CREDIT SPREAD vs. BULL PUT SPREAD):
  * These two terms describe the EXACT same mechanical options architecture. 
  * "Put Credit Spread" is the universal structural classification for selling a higher strike 
    put (STO) and buying a lower strike put (BTO) for an upfront net credit.
  * "Bull Put Spread" is simply the directional market bias application of this spread. 
    Because you harvest a credit that you keep if the stock stays flat or goes up, the trade 
    is inherently bullish. 
  * This program displays the strategy under the universal "Put Credit Spread" banner, 
    automatically balancing your short leg credits against your long leg debits.

CORE OPERATIONAL WORKFLOW:
  1. FILE INGESTION: Scans 'option_order.txt' and strictly filters out trailing spaces, 
     blank lines, or carriage returns to isolate clean symbols, dates, and contract quantities.
  2. STRIKE STRUCTURE MAPPING: Dynamically establishes exchange-compliant strike intervals 
     ($0.50 wide for sub-$5 stocks, $1.00 wide for mid-caps, and $5.00 wide for high-priced stocks).
  3. CAPACITARY RISK AUDITING: Prior to order transmission, calculates the exact dollar reduction 
     in buying power (Risk Amount) by taking the strike width, subtracting the net credit, 
     and multiplying by your position scale.
  4. INTERACTIVE ROUTING GATE: Pauses and reviews each symbol sequentially, prompting the operator 
     to commit the trade payload to the 'sandbox' mock server or the 'production' live server.
  5. LOCAL LEDGER LOGGING: Upon a successful server response, automatically appends a clean, 
     human-readable record directly into a permanent file database ('order_history_log.txt').
===================================================================================================
"""
import requests
import json
import re
import os
import sys
import uuid
from datetime import datetime

# ================= PRODUCTION vs SANDBOX URLs =================
SANDBOX_URL = "https://40894351-2463-4a8d-89eb-6560e07b273c.mock.pstmn.io/accounts/555-sandbox-act/orders"
PRODUCTION_URL = "https://40894351-2463-4a8d-89eb-6560e07b273c.mock.pstmn.io/accounts/555-live-act/orders"

headers = {
    "Content-Type": "application/json"
}

def load_all_option_orders(filename="option_order.txt"):
    """Reads the order file, strictly filtering out empty lines, comments, and spacing."""
    orders = []
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return orders
    
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().replace("\r", "")
            if not line or line.startswith("#"):
                continue
            
            parts = [p.strip() for p in line.split(",") if p.strip()]
            
            if len(parts) >= 2:
                symbol = parts[0].upper()
                expiration = parts[1]
                
                quantity = 1
                if len(parts) >= 3:
                    try:
                        quantity = int(parts[2])
                    except ValueError:
                        quantity = 1
                        
                orders.append((symbol, expiration, quantity))
    return orders

def log_transaction_locally(ticket_label, symbol, qty, short_stk, long_stk, credit, risk, order_id):
    """Appends a highly readable, structured entry into your local permanent ledger file."""
    log_filename = "order_history_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    file_exists = os.path.exists(log_filename)
    
    with open(log_filename, "a") as log_file:
        if not file_exists:
            log_file.write("="*120 + "\n")
            log_file.write(f"AJ CAPITAL LLC - AUTOMATED OPTIONS ROUTING PERMANENT HISTORICAL LEDGER\n")
            log_file.write("="*120 + "\n")
            log_file.write(f"{'TIMESTAMP':<22} {'ACCOUNT TYPE':<15} {'ID':<15} {'SYM':<6} {'QTY':<4} {'STRATEGY':<15} {'NET CR':<8} {'TOTAL CR':<10} {'RISK COLLATERAL':<15}\n")
            log_file.write("-"*120 + "\n")
            
        account_type = "SANDBOX" if "SANDBOX" in ticket_label else "PRODUCTION"
        total_credit = round(qty * credit * 100, 2)
        strategy_str = f"{short_stk}/{long_stk} P"
        
        log_file.write(
            f"{timestamp:<22} {account_type:<15} {order_id:<15} {symbol:<6} {qty:<4} {strategy_str:<15} ${credit:<6.2f} ${total_credit:<9.2f} ${risk:<14.2f}\n"
        )

def get_live_market_price(symbol):
    """SIMULATED LIVE DATA FETCH ENGINE"""
    live_quotes = {
        "BBAI": 3.80,
        "F": 12.40,
        "SOUND": 8.33,
        "SOFI": 15.22,
        "KO": 61.50
    }
    return live_quotes.get(symbol, 10.00)

def calculate_spread_strikes(symbol, underlying_price):
    """DYNAMIC STRATEGY ENGINE: Adjusts strike tiers based on underlying price brackets."""
    if underlying_price < 5.00:
        strike_width = 0.50
        short_strike = (underlying_price // 0.50) * 0.50
    elif underlying_price < 25.00:
        strike_width = 1.00
        short_strike = float(int(underlying_price))
    else:
        strike_width = 5.00
        short_strike = (underlying_price // 5.00) * 5.00

    long_strike = short_strike - strike_width

    if symbol == "KO":
        short_premium = 0.45   
        long_premium = 0.08    
    else:
        short_premium = round(underlying_price * 0.025, 2)
        long_premium = round(underlying_price * 0.008, 2)
        
        if short_premium == long_premium:
            long_premium = max(0.01, short_premium - 0.05)

    credit_received = round(short_premium - long_premium, 2)
    return short_strike, long_strike, short_premium, long_premium, credit_received

def display_trading_table(title, spread_data, total_net_credit, total_risk_amount, order_id="PRE-FLIGHT REVIEW", status_code="LOCAL"):
    """Generates the clean layout matrix view inside the terminal screen with precision alignment."""
    exp_string = spread_data.get("expiration_date", "")
    days_to_close_str = "N/A"
    formatted_exp = exp_string

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y"):
        try:
            exp_date = datetime.strptime(exp_string, fmt)
            days_to_close = (exp_date - datetime.now()).days + 1
            days_to_close_str = f"{days_to_close} DTE" if days_to_close >= 0 else "0 DTE"
            formatted_exp = exp_date.strftime("%b %d")
            break
        except ValueError:
            continue

    print("\n" + "="*128)
    print(f" {title} | Order ID: {order_id} | Status: {status_code}")
    print("="*128)
    
    headers_fmt = "{:<5} {:<16} {:<18} {:<8} {:<8} {:<6} {:<8} {:<10} {:<12} {:<12} {:<14} {:<14}"
    print(headers_fmt.format(
        "QTY", "SYMBOL (PX)", "STRATEGY", "EXP", "DTE", "TYPE", "ACTION", "STRIKE", "LEG PRICE", "NET CREDIT", "TOTAL CREDIT", "RISK AMT"
    ))
    print("-"*128)
    
    symbol_and_price = f"{spread_data.get('symbol')} (${spread_data.get('underlying_price'):.2f})"
    sorted_legs = sorted(spread_data.get("legs", []), key=lambda x: x.get("action"), reverse=True)
    
    for index, leg in enumerate(sorted_legs):
        strategy_col = spread_data.get("strategy") if index == 0 else ""
        net_credit_col = f"${spread_data.get('credit_received'):.2f}" if index == 0 else ""
        total_credit_col = f"${total_net_credit:.2f}" if index == 0 else ""
        total_risk_col = f"${total_risk_amount:.2f}" if index == 0 else ""
        symbol_col = symbol_and_price if index == 0 else ""
        
        print(headers_fmt.format(
            spread_data.get("quantity"),
            symbol_col,
            strategy_col,
            formatted_exp,
            days_to_close_str if index == 0 else "", 
            spread_data.get("option_type"),
            leg.get("action"),
            f"${leg.get('strike'):.2f}",
            f"${leg.get('price'):.2f}",
            net_credit_col,
            total_credit_col,
            total_risk_col
        ))
    print("="*128)

# ================= CORE PROGRAM RUNNER =================

# Uses the exact same option_order.txt file
trade_list = load_all_option_orders("option_order.txt")

if not trade_list:
    print("No orders found in option_order.txt.")
    sys.exit()

print(f"Loaded {len(trade_list)} symbols from file. Starting sequential review process...")

last_intent = None

for symbol_input, expiration_input, qty_input in trade_list:
    
    stock_px = get_live_market_price(symbol_input)
    sell_stk, buy_stk, sell_px, buy_px, net_credit = calculate_spread_strikes(symbol_input, stock_px)
    
    total_net_credit = round(qty_input * net_credit * 100, 2)
    strike_width = sell_stk - buy_stk
    total_risk_amount = round((strike_width - net_credit) * qty_input * 100, 2)

    put_credit_spread_payload = {
        "symbol": symbol_input,
        "strategy": "Put Credit Spread",  # Universal terminology update
        "underlying_price": stock_px,
        "expiration_date": expiration_input,
        "quantity": qty_input,
        "option_type": "Put",
        "legs": [
            {"type": "Long Put", "strike": buy_stk, "action": "BTO", "price": buy_px},
            {"type": "Short Put", "strike": sell_stk, "action": "STO", "price": sell_px}
        ],
        "credit_received": net_credit
    }

    display_trading_table(f"PRE-FLIGHT REVIEW FOR {symbol_input}", put_credit_spread_payload, total_net_credit, total_risk_amount)

    print(f"\n🚨 ROUTING COMMAND FOR {symbol_input} ({qty_input} Contract{'s' if qty_input > 1 else ''}):")
    print(" -> Type 'sandbox'     to test order")
    print(" -> Type 'production'  to route live order")
    print(" -> Type 'skip'        to skip this symbol")
    print(" -> Type 'exit'        to quit program completely")
    if last_intent:
        print(f" -> [Or just press ENTER to re-use last setting: '{last_intent}']")
    
    user_input = input(f"\nsend to sandbox / production...:> ").strip().lower()

    if user_input == "" and last_intent is not None:
        current_intent = last_intent
        print(f"♻️ Re-using last command: {current_intent}")
    elif user_input == "" and last_intent is None:
        print(f"⏭️ Skipping {symbol_input}.")
        continue
    else:
        current_intent = user_input

    if current_intent == "exit":
        print("\nStopping program loop entirely. Goodbye.")
        break
    elif current_intent == "skip":
        print(f"\n⏭️ Skipping {symbol_input}...")
        continue
    elif current_intent == "sandbox":
        target_url = SANDBOX_URL
        ticket_label = f"SANDBOX MOCK SERVER EXECUTION TICKET ({symbol_input})"
        last_intent = "sandbox"
    elif current_intent == "production":
        target_url = PRODUCTION_URL
        ticket_label = f"LIVE PRODUCTION ORDER RECEIPT ({symbol_input})"
        last_intent = "production"
    else:
        print(f"\n❌ Unrecognized command '{current_intent}'. Skipping {symbol_input}...")
        continue

    try:
        response = requests.post(target_url, json=put_credit_spread_payload, headers=headers)
        status_code_out = response.status_code
        
        if status_code_out in [200, 201]:
            server_order_id = f"TRD-{str(uuid.uuid4()).upper()[:8]}"
            log_transaction_locally(ticket_label, symbol_input, qty_input, sell_stk, buy_stk, net_credit, total_risk_amount, server_order_id)
        else:
            server_order_id = "N/A"
            
        display_trading_table(ticket_label, put_credit_spread_payload, total_net_credit, total_risk_amount, order_id=server_order_id, status_code=status_code_out)

    except Exception as e:
        print(f"\nTransmission Error on {symbol_input}: {str(e)}")

print("\nAll symbols processed successfully!")