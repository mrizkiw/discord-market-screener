import requests
import time
import threading
from config import BINANCE_BASE_URL, CACHE_TTL

class BinanceClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BinanceClient, cls).__new__(cls)
                cls._instance._init_once()
            return cls._instance

    def _init_once(self):
        self.base_url = BINANCE_BASE_URL
        self._exchange_info_cache = None
        self._exchange_info_timestamp = 0
    
    def get_exchange_info(self):
        # Basic cache to avoid rate limits with TTL
        now = time.time()
        if self._exchange_info_cache and (now - self._exchange_info_timestamp < CACHE_TTL):
            return self._exchange_info_cache
        
        url = f"{self.base_url}/api/v3/exchangeInfo"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        self._exchange_info_cache = data
        self._exchange_info_timestamp = now
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

    def get_24hr_tickers(self):
        url = f"{self.base_url}/api/v3/ticker/24hr"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
