import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
from services.binance_client import BinanceClient

SCANNER_CACHE_FILE = "daily_picks.json"

class ScannerService:
    def __init__(self):
        self.client = BinanceClient()
        self.daily_picks = self._load_cache()
        
    def _load_cache(self) -> dict:
        if not os.path.exists(SCANNER_CACHE_FILE):
            return {"date": "", "symbols": []}
        try:
            with open(SCANNER_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {"date": "", "symbols": []}
            
    def _save_cache(self, date_str: str, symbols: List[str]):
        data = {"date": date_str, "symbols": symbols}
        with open(SCANNER_CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        self.daily_picks = data
            
    def get_daily_picks(self) -> List[str]:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        if self.daily_picks.get("date") != today or not self.daily_picks.get("symbols"):
            self.refresh_daily_picks()
        return self.daily_picks.get("symbols", [])
        
    def refresh_daily_picks(self, limit: int = 5):
        try:
            tickers = self.client.get_24hr_tickers()
            
            # Filter criteria:
            # 1. Ends with USDT
            # 2. Not leveraged tokens (UP/DOWN/BULL/BEAR)
            # 3. Positive price change
            # 4. Sort by quoteVolume (highest liquidity)
            
            valid_tickers = []
            for t in tickers:
                symbol = t['symbol']
                if not symbol.endswith('USDT'):
                    continue
                if any(x in symbol for x in ['UPUSDT', 'DOWNUSDT', 'BULLUSDT', 'BEARUSDT', 'USDCUSDT', 'FDUSDUSDT']):
                    continue
                    
                price_change = float(t['priceChangePercent'])
                quote_volume = float(t['quoteVolume'])
                
                # Only looking for coins that are moving (e.g. > 3% but < 30% to avoid extreme pumps)
                # and have decent volume
                if 3.0 <= price_change <= 30.0 and quote_volume > 10000000:
                    valid_tickers.append({
                        "symbol": symbol,
                        "change": price_change,
                        "volume": quote_volume
                    })
                    
            # Sort by volume descending
            valid_tickers.sort(key=lambda x: x['volume'], reverse=True)
            
            top_symbols = [t['symbol'] for t in valid_tickers[:limit]]
            
            # Save to cache
            today = datetime.utcnow().strftime('%Y-%m-%d')
            self._save_cache(today, top_symbols)
            
        except Exception as e:
            print(f"Error refreshing daily picks: {e}")
