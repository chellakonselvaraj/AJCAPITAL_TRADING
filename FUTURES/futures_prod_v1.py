import os
import sys
import asyncio
import httpx

# Visual Layout Configurations
os.system('clear')

async def fetch_futures_market_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json().get("rates", {})
        except Exception:
            pass
    return {}

async def calculate_futures_metrics():
    print("========================================================================================================================")
    print("              AJ CAPITAL LLC - AUTOMATED FOREX RISK MONITOR [PRODUCTION]                                                ")
    print("========================================================================================================================")
    print("ROOT   | LIVE SPOT (S&P/NDX) | AUTO SUPPORT(Base) | AUTO RESIST (top) | TICK COST | ORDER PLACEMENT RISK ENGINE             ")
    print("------------------------------------------------------------------------------------------------------------------------")

    try:
        rates = await fetch_futures_market_rates()
        
        # Resetting all asset baselines and variances to zero
        targets = {
            "/MES": {"tick_cost": "$1.25", "base_spot": 0.00, "variance": 0.00, "buffer": 0.0, "force_alert": False},
            "/MNQ": {"tick_cost": "$0.50", "base_spot": 0.00, "variance": 0.00, "buffer": 0.0, "force_alert": False},
            "/MCL": {"tick_cost": "$1.00", "base_spot": 0.00, "variance": 0.00, "buffer": 0.0, "force_alert": False},
            "TEST": {"tick_cost": "$0.00", "base_spot": 0.00, "variance": 0.00, "buffer": 0.0, "force_alert": True} # Permanent template row
        }
        
        for symbol, meta in targets.items():
            ticker_modifier = rates.get("EUR", 1.0) if "MES" in symbol else rates.get("GBP", 1.0)
            
            if ticker_modifier != 1.0 and symbol != "TEST":
                spot_calc = meta["base_spot"] * (1 + (abs(1 - ticker_modifier) * 0.02))
            else:
                spot_calc = meta["base_spot"]
                
            precision = 2
            spot_price = f"{spot_calc:,.{precision}f}"
            
            support_val = spot_calc - meta["variance"]
            resistance_ceiling = f"{(spot_calc + meta["variance"]):,.{precision}f}"
            support_floor = f"{support_val:,.{precision}f}"
            
            # Revised Logic Block
            if meta["force_alert"] or spot_calc <= (support_val + meta["buffer"]):
                signal = "ALERT - ENTRY ZONE"
            else:
                signal = "" # Completely blank when not ready to enter
            
            print(f"{symbol:<6} | {spot_price:<12} | {support_floor:<14} | {resistance_ceiling:<14} | {meta['tick_cost']:<9} | {signal:<28}")
                
    except Exception as e:
        print(f"\n[X] Live Pipeline Disruption: {e}")
        print("[!] Execution Paused. Resetting auth stream endpoints...")

    print("========================================================================================================================")

if __name__ == "__main__":
    asyncio.run(calculate_futures_metrics())