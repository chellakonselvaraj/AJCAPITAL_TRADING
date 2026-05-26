import os
import sys
import asyncio
from decimal import Decimal
from tastytrade import Session

async def build_futures_specification_matrix():
    # 1. Authenticate Infrastructure Session
    client_secret = os.environ.get("TASTY_CLIENT_SECRET")
    refresh_token = os.environ.get("TASTY_REFRESH_TOKEN")
    
    if not client_secret or not refresh_token:
        print("CRITICAL ERROR: Environment variables missing in this terminal session.")
        sys.exit(1)

    # Establish connection to confirm operational session status
    session = Session(client_secret, refresh_token)
    
    print("=" * 160)
    print(f" EXCHANGE SPECIFICATION MATRIX - MICRO, E-MINI & STANDARD CONTRACT CODES")
    print("=" * 160)
    print(f"{'Root':<6} | {'Type':<10} | {'Short Symbol':<13} | {'Full Clearing Symbol':<22} | {'Long Name (Description)':<32} | {'Tick Size':<9} | {'Tick Value':<11} | {'Point Value'}")
    print("-" * 160)

    # Dynamic year assignment based on our current 2026 trading timeline
    current_year_long = "2026"
    current_year_short = "6"
    active_month_letter = "M"  # June Expiration
    
    combined_code_short = f"{active_month_letter}{current_year_short}"  # e.g., M6
    
    # Core CME/ICE specification parameters hardcoded directly for absolute data stability
    target_futures_matrix = [
        # --- Equity Micros ($2.00 / $5.00 per point formulas) ---
        {"root": "MNQ", "type": "Micro", "desc": "Micro E-mini Nasdaq-100", "tick_size": "0.25", "point_val": "2.00"},
        {"root": "MES", "type": "Micro", "desc": "Micro E-mini S&P 500", "tick_size": "0.25", "point_val": "5.00"},
        {"root": "MYM", "type": "Micro", "desc": "Micro E-mini Dow Jones", "tick_size": "1.00", "point_val": "0.50"},
        {"root": "M2K", "type": "Micro", "desc": "Micro E-mini Russell 2000", "tick_size": "0.10", "point_val": "5.00"},
        
        # --- Equity E-Minis ($20.00 / $50.00 per point formulas) ---
        {"root": "NQ",  "type": "E-Mini", "desc": "E-mini Nasdaq-100", "tick_size": "0.25", "point_val": "20.00"},
        {"root": "ES",  "type": "E-Mini", "desc": "E-mini S&P 500", "tick_size": "0.25", "point_val": "50.00"},
        {"root": "YM",  "type": "E-Mini", "desc": "E-mini Dow Jones", "tick_size": "1.00", "point_val": "5.00"},
        {"root": "RTY", "type": "E-Mini", "desc": "E-mini Russell 2000", "tick_size": "0.10", "point_val": "50.00"},
        
        # --- Commodities & Energy ---
        {"root": "MCL", "type": "Micro", "desc": "Micro Crude Oil", "tick_size": "0.01", "point_val": "100.00"},
        {"root": "CL",  "type": "Standard", "desc": "Crude Oil Light Sweet", "tick_size": "0.01", "point_val": "1000.00"},
        {"root": "MGC", "type": "Micro", "desc": "Micro Gold", "tick_size": "0.10", "point_val": "10.00"},
        {"root": "GC",  "type": "Standard", "desc": "Gold COMEX", "tick_size": "0.10", "point_val": "100.00"},
        {"root": "M6E", "type": "Micro", "desc": "Micro Euro Currency", "tick_size": "0.0001", "point_val": "125000.00"},
        {"root": "6E",  "type": "Standard", "desc": "Euro FX Currency", "tick_size": "0.0005", "point_val": "125000.00"}
    ]

    for item in target_futures_matrix:
        root_code = item["root"]
        contract_type = item["type"]
        long_name = item["desc"]
        
        # Build the symbols dynamically
        short_symbol = f"/{root_code}{combined_code_short}"
        clearing_symbol = f"{root_code}{active_month_letter}{current_year_long}"
        
        # Calculate true dollar values per tick move
        tick_size = Decimal(item["tick_size"])
        point_multiplier = Decimal(item["point_val"])
        tick_value = point_multiplier * tick_size
        
        # Format strings for clean visual grid layout matching
        tick_size_str = f"{tick_size}"
        if root_code == "M6E":
            tick_size_str = "0.0001"
            
        print(f"{root_code:<6} | {contract_type:<10} | {short_symbol:<13} | {clearing_symbol:<22} | {long_name:<32} | {tick_size_str:<9} | ${tick_value:<10,.2f} | ${point_multiplier:,.2f}")
        
        # Adds an empty line after every single row to double-space the layout cleanly
        print()
if __name__ == "__main__":
    asyncio.run(build_futures_specification_matrix())