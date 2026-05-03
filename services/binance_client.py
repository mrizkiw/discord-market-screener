import requests
from config import BINANCE_BASE_URL

class BinanceClient:
    def __init__(self):
        self.base_url = BINANCE_BASE_URL
        self._exchange_info_cache = None
    
    def get_exchange_info(self):
        # Basic cache to avoid rate limits
        if self._exchange_info_cache:
            return self._exchange_info_cache
        
        url = f"{self.base_url}/api/v3/exchangeInfo"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        self._exchange_info_cache = data
        return data

    def get_symbol_info(self, symbol: str):
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                return s
        return None

    def get_klines(self, symbol: str, interval: str, limit: int = 100):
        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
