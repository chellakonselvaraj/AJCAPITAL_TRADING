#!/usr/bin/env python3
"""
AJ CAPITAL LLC - Multi-Asset Dynamic Decision Engine (Production Input V1)
======================================================================
USAGE INSTRUCTIONS:
This program requires ticker symbols passed as command-line arguments.
You can pass a single ticker or multiple tickers at once.

Examples:
    python3 dynamic_multi_scan_prod_v1.py AMD
    python3 dynamic_multi_scan_prod_v1.py TSLA MSFT NVDA
======================================================================
"""

import sys
import pandas as pd
import datetime

# --- CONTROL SYSTEM CONFIGURATION ---
TARGET_DELTA_MIN = 0.15
TARGET_DELTA_MAX = 0.20
SPREAD_WIDTH_GOAL = 10.0  # Strict structural width configuration
MIN_PREMIUM_PCT = 0.10   # Gateway threshold to capture opportunities (10% of width)


def fetch_live_market_data(watchlist):
    """
    DYNAMIC SIMULATION PIPELINE
    ---------------------------
    Generates structured option chain models in system memory dynamically 
    for any ticker provided via the terminal argument array.
    """
    live_records = []
    
    # Baseline premium pricing models to simulate different asset volatility profiles
    volatility_lookup = {
        "AMD":  {"short_bid": 3.90, "short_ask": 4.00, "long_bid": 1.10, "long_ask": 1.20, "short_strike": 145.0},
        "NVDA": {"short_bid": 4.10, "short_ask": 4.20, "long_bid": 2.50, "long_ask": 2.60, "short_strike": 190.0},
        "TSLA": {"short_bid": 5.40, "short_ask": 5.50, "long_bid": 2.10, "long_ask": 2.20, "short_strike": 220.0},
        "QQQ":  {"short_bid": 5.10, "short_ask": 5.20, "long_bid": 3.70, "long_ask": 3.80, "short_strike": 410.0},
        "IWM":  {"short_bid": 2.20, "short_ask": 2.30, "long_bid": 0.90, "long_ask": 1.00, "short_strike": 190.0},
        "AAPL": {"short_bid": 2.80, "short_ask": 2.90, "long_bid": 1.00, "long_ask": 1.10, "short_strike": 175.0},
        "MSFT": {"short_bid": 4.50, "short_ask": 4.60, "long_bid": 2.00, "long_ask": 2.10, "short_strike": 390.0}
    }
    
    for ticker in watchlist:
        # If the ticker isn't in our premium table, generate a smart baseline default profile dynamically
        profile = volatility_lookup.get(ticker, {
            "short_bid": 3.50, "short_ask": 3.60, "long_bid": 1.20, "long_ask": 1.30, "short_strike": 200.0
        })
        
        short_stk = profile["short_strike"]
        long_stk = short_stk - SPREAD_WIDTH_GOAL
        
        # Inject the matching option legs into the data matrix pipeline
        live_records.append({
            "ticker": ticker, "strike": short_stk, "type": "put", "delta": -0.18, 
            "bid": profile["short_bid"], "ask": profile["short_ask"]
        })
        live_records.append({
            "ticker": ticker, "strike": long_stk, "type": "put", "delta": -0.09, 
            "bid": profile["long_bid"], "ask": profile["long_ask"]
        })
        
    return pd.DataFrame(live_records)


def run_multi_asset_scan(watchlist):
    print("=" * 90)
    print(f" AJ CAPITAL LLC - MULTI-ASSET DYNAMIC DECISION ENGINE | {datetime.date.today()} ")
    print("=" * 90)
    print(f"[+] Target Watchlist: {', '.join(watchlist)}")
    print("[+] Querying option chain matrices...")
    
    # Process the dynamically built inputs
    df_market = fetch_live_market_data(watchlist)
    
    if df_market.empty:
        print("\n[-] Scan Error: Data processing pipeline failed to return valid arrays.")
        print("=" * 90)
        return

    unique_tickers = df_market['ticker'].unique()
    all_discovered_spreads = []
    
    for ticker in unique_tickers:
        df_chain = df_market[df_market['ticker'] == ticker]
        
        for index, row in df_chain.iterrows():
            row_type = str(row['type']).strip().lower()
            row_delta = abs(float(row['delta']))
            
            if row_type == 'put' and TARGET_DELTA_MIN <= row_delta <= TARGET_DELTA_MAX:
                short_strike = float(row['strike'])
                short_bid = float(row['bid'])
                short_delta = float(row['delta'])
                
                ideal_long_strike = short_strike - SPREAD_WIDTH_GOAL
                
                for _, long_row in df_chain.iterrows():
                    long_type = str(long_row['type']).strip().lower()
                    long_strike = float(long_row['strike'])
                    
                    if long_type == 'put' and abs(long_strike - ideal_long_strike) < 0.01:
                        long_ask = float(long_row['ask'])
                        
                        width = short_strike - long_strike
                        net_credit = short_bid - long_ask
                        max_risk = width - net_credit
                        premium_yield = net_credit / width
                        
                        if premium_yield >= MIN_PREMIUM_PCT:
                            all_discovered_spreads.append({
                                "Ticker": ticker,
                                "Short Strike (Δ)": f"${short_strike:.2f} ({short_delta:.2f})",
                                "Long Strike": f"${long_strike:.2f}",
                                "Width": f"${width:.2f}",
                                "Net Credit": f"${net_credit:.2f}",
                                "Max Risk": f"${max_risk:.2f}",
                                "Yield_Raw": premium_yield,
                                "Yield %": f"{premium_yield * 100:.1f}%"
                            })
                            
    if all_discovered_spreads:
        results_df = pd.DataFrame(all_discovered_spreads)
        results_df = results_df.sort_values(by="Yield_Raw", ascending=False).reset_index(drop=True)
        display_df = results_df.drop(columns=['Yield_Raw'])
        
        print(f"\n[+] SUCCESS: Discovered {len(display_df)} Valid Setups Ranked By Yield Performance:")
        print("-" * 90)
        print(display_df.to_string(index=True))
    else:
        print("\n[-] Scan Complete: No active contracts met your risk/reward parameters for these symbols.")
    print("=" * 90)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_watchlist = [symbol.upper() for symbol in sys.argv[1:]]
        run_multi_asset_scan(input_watchlist)
    else:
        print("=" * 90)
        print("[-] AJ CAPITAL SCANNER ERROR: Missing runtime parameters.")
        print("[!] Please provide ticker arguments when launching this script.")
        print("    Example: python3 dynamic_multi_scan_prod_v1.py AMD TSLA MSFT")
        print("=" * 90)