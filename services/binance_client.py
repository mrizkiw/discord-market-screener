import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import threading
from config import BINANCE_BASE_URL, CACHE_TTL


def _create_session() -> requests.Session:
    """Create a requests.Session with retry logic and connection pooling."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,                    # Retry max 3x
        backoff_factor=1,           # Wait 1s, 2s, 4s between retries
        status_forcelist=[500, 502, 503, 504],  # Retry on server errors
        allowed_methods=["GET"],    # Hanya retry GET requests
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,        # Connection pool size
        pool_maxsize=20,            # Max connections in pool
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Default headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; TradingBot/1.0)",
        "Accept": "application/json",
    })

    return session


class BinanceClient:
    _instance = None
    _lock = threading.Lock()

    # Default timeout: (connect_timeout, read_timeout) in seconds
    DEFAULT_TIMEOUT = (10, 30)

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BinanceClient, cls).__new__(cls)
                cls._instance._init_once()
            return cls._instance

    def _init_once(self):
        self.base_url = BINANCE_BASE_URL
        self.session = _create_session()
        self._exchange_info_cache = None
        self._exchange_info_timestamp = 0

    def get_exchange_info(self):
        # Basic cache to avoid rate limits with TTL
        now = time.time()
        if self._exchange_info_cache and (now - self._exchange_info_timestamp < CACHE_TTL):
            return self._exchange_info_cache

        url = f"{self.base_url}/api/v3/exchangeInfo"
        response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
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
        response = self.session.get(url, params=params, timeout=self.DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_24hr_tickers(self):
        url = f"{self.base_url}/api/v3/ticker/24hr"
        response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
