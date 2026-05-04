import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BINANCE_BASE_URL = "https://api.binance.com"
DEFAULT_TIMEFRAME = "30m"
DEFAULT_CANDLE_LIMIT = 100
CACHE_TTL = 60  # seconds
