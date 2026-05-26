import os
import sys
import asyncio
import httpx

os.system('clear')

async def fetch_spot_rates():
    # Rapid endpoint backup to secure true global spot fx prices independent of broker data holds
    url = "https://open.er-api.com/v6/latest/USD"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("rates", {})
        return {}

async def run_forex_monitor():
    print("=======================================================================================================================")
    print("                AJ CAPITAL LLC - AUTOMATED FOREX 10-PIP BUFFER RISK MONITOR [PRODUCTION]")
    print("=======================================================================================================================")
    print(f"{'PAIR':<8} | {'LIVE SPOT':<13} | {'AUTO SUPP':<11} | {'10-PIP BUY':<10} | {'AUTO RESIS':<10} | {'PIP VAL':<8} | {'STRATEGY SIGNAL ENGINE':<22}")
    print("-----------------------------------------------------------------------------------------------------------------------")

    try:
        rates = await fetch_spot_rates()
        
        # Core pair profiles and hardcoded pip value allocations
        pairs_config = {
            "EUR/USD": {"pip_val": "$1.00", "base_multiplier": 1.0},
            "GBP/USD": {"pip_val": "$1.00", "base_multiplier": 1.2},
            "AUD/USD": {"pip_val": "$1.00", "base_multiplier": 0.6},
            "USD/JPY": {"pip_val": "$100.00", "base_multiplier": 150.0}
        }
        
        for pair, config in pairs_config.items():
            # Parse rate mapping
            if pair == "EUR/USD" and "EUR" in rates:
                # Convert base USD rate to inverse for quoting convention
                spot = round(1 / rates["EUR"], 5)
            elif pair == "GBP/USD" and "GBP" in rates:
                spot = round(1 / rates["GBP"], 5)
            elif pair == "AUD/USD" and "AUD" in rates:
                spot = round(1 / rates["AUD"], 5)
            elif pair == "USD/JPY" and "JPY" in rates:
                spot = round(rates["JPY"], 3)
            else:
                spot = config["base_multiplier"] # Fallback structural baseline
                
            # Precision math calculating your 10-PIP Strategy Buffer
            pip_size = 0.0001 if "JPY" not in pair else 0.01
            auto_support = round(spot - (pip_size * 5), 5 if "JPY" not in pair else 3)
            ten_pip_buy = round(auto_support + (pip_size * 10), 5 if "JPY" not in pair else 3)
            auto_resist = round(spot + (pip_size * 15), 5 if "JPY" not in pair else 3)
            
            signal = "STANDBY - BUFFER CLEAR" if spot > ten_pip_buy else "ALERT - ENTRY ZONE"
            
            print(f"{pair:<8} | {spot:<13} | {auto_support:<11} | {ten_pip_buy:<10} | {auto_resist:<10} | {config['pip_val']:<8} | {signal:<22}")
            
    except Exception as e:
        print(f"[X] Internal Engine Exception: {e}")
        
    print("=======================================================================================================================")

if __name__ == "__main__":
    asyncio.run(run_forex_monitor())