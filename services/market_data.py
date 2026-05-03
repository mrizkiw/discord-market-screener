import pandas as pd
from typing import Optional
from services.binance_client import BinanceClient
from models.market import SymbolMeta

class MarketDataService:
    def __init__(self):
        self.client = BinanceClient()

    def fetch_symbol_meta(self, symbol: str) -> Optional[SymbolMeta]:
        info = self.client.get_symbol_info(symbol)
        if not info:
            return None
        
        # Parse tick_size and step_size
        tick_size = 0.0
        step_size = 0.0
        for f in info.get("filters", []):
            if f["filterType"] == "PRICE_FILTER":
                tick_size = float(f["tickSize"])
            elif f["filterType"] == "LOT_SIZE":
                step_size = float(f["stepSize"])
                
        return SymbolMeta(
            symbol=info["symbol"],
            status=info["status"],
            quote_asset=info["quoteAsset"],
            tick_size=tick_size,
            step_size=step_size
        )

    def fetch_candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        data = self.client.get_klines(symbol, interval, limit)
        columns = [
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ]
        df = pd.DataFrame(data, columns=columns)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
        df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
        
        # Convert numeric columns
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df
