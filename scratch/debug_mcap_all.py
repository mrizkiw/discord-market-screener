from analysis.marketcap import fetch_marketcap_data, SYMBOL_TO_COINGECKO_ID, format_market_cap
import time

print(f"{'Symbol':<12} | {'Price 24h':<10} | {'MCap 24h':<10} | {'Div':<8} | {'Signal'}")
print("-" * 65)

for symbol in list(SYMBOL_TO_COINGECKO_ID.keys()):
    try:
        r = fetch_marketcap_data(symbol)
        div = r.market_cap_change_24h - r.price_change_24h
        print(f"{symbol:<12} | {r.price_change_24h:>9.2f}% | {r.market_cap_change_24h:>9.2f}% | {div:>+7.2f}% | {r.signal}")
        time.sleep(1.2) # Avoid rate limits
    except Exception as e:
        print(f"{symbol:<12} | Error: {e}")
