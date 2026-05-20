"""
Market Cap Analysis Module
Mendeteksi sinyal akumulasi: market cap naik tapi harga flat/turun.
Menggunakan CoinGecko API (gratis, tanpa API key).
"""

import requests
import time
import threading
from dataclasses import dataclass
from typing import Optional

# Simple in-memory cache untuk CoinGecko (rate limit: 10-30 req/min)
_cache: dict = {}
_cache_lock = threading.Lock()
COINGECKO_CACHE_TTL = 300  # 5 menit

# Mapping simbol Binance → CoinGecko coin ID (untuk coin umum)
# CoinGecko akan di-fallback ke search jika tidak ada di sini
SYMBOL_TO_COINGECKO_ID = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "BNBUSDT": "binancecoin",
    "SOLUSDT": "solana",
    "XRPUSDT": "ripple",
    "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin",
    "AVAXUSDT": "avalanche-2",
    "DOTUSDT": "polkadot",
    "LINKUSDT": "chainlink",
    "LTCUSDT": "litecoin",
    "UNIUSDT": "uniswap",
    "MATICUSDT": "matic-network",
    "SHIBUSDT": "shiba-inu",
    "TRXUSDT": "tron",
    "ATOMUSDT": "cosmos",
    "NEARUSDT": "near",
    "INJUSDT": "injective-protocol",
    "SUIUSDT": "sui",
    "ARBUSDT": "arbitrum",
    "OPUSDT": "optimism",
    "APTUSDT": "aptos",
    "FILUSDT": "filecoin",
    "ICPUSDT": "internet-computer",
    "STXUSDT": "blockstack",
    "RUNEUSDT": "thorchain",
    "AAVEUSDT": "aave",
    "SEIUSDT": "sei-network",
    "TIAUSDT": "celestia",
    "FETUSDT": "fetch-ai",
    "RENDERUSDT": "render-token",
    "WIFUSDT": "dogwifcoin",
    "BONKUSDT": "bonk",
    "PEPEUSDT": "pepe",
    "FLOKIUSDT": "floki",
    "ASTERUSDT": "aster-2",
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


@dataclass
class MarketCapResult:
    """Hasil analisa perbandingan market cap vs harga."""
    coin_id: str                        # CoinGecko coin ID
    current_price: float                # Harga saat ini (USD)
    market_cap: float                   # Market cap saat ini (USD)
    price_change_24h: float             # % perubahan harga 24h
    market_cap_change_24h: float        # % perubahan market cap 24h
    signal: str                         # "accumulation", "distribution", "aligned_up", "aligned_down", "neutral"
    signal_label: str                   # Label yang mudah dibaca
    signal_emoji: str                   # Emoji representasi
    interpretation: str                 # Penjelasan singkat
    available: bool = True              # False jika data tidak tersedia


def _get_cached(key: str) -> Optional[dict]:
    """Ambil data dari cache jika masih valid."""
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"] < COINGECKO_CACHE_TTL):
            return entry["data"]
    return None


def _set_cache(key: str, data: dict):
    """Simpan data ke cache."""
    with _cache_lock:
        _cache[key] = {"ts": time.time(), "data": data}


def _resolve_coin_id(symbol: str) -> Optional[str]:
    """
    Resolve simbol Binance ke CoinGecko coin ID.
    Pertama cek mapping statis, lalu search via API.
    """
    # Normalisasi: hilangkan USDT suffix
    symbol = symbol.upper()
    
    # Cek mapping statis dulu
    if symbol in SYMBOL_TO_COINGECKO_ID:
        return SYMBOL_TO_COINGECKO_ID[symbol]
    
    # Fallback: search CoinGecko
    base = symbol.replace("USDT", "").replace("BTC", "").replace("ETH", "").replace("BNB", "")
    cache_key = f"search_{base}"
    cached = _get_cached(cache_key)
    if cached:
        return cached.get("id")
    
    try:
        resp = requests.get(
            f"{COINGECKO_BASE}/search",
            params={"query": base},
            timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("coins", [])
        if results:
            coin_id = results[0]["id"]
            _set_cache(cache_key, {"id": coin_id})
            return coin_id
    except Exception:
        pass
    
    return None


def fetch_marketcap_data(symbol: str) -> MarketCapResult:
    """
    Ambil data market cap dari CoinGecko dan analisa sinyal akumulasi/distribusi.
    
    Signal Logic:
    - ACCUMULATION: market_cap_change > price_change + 3%  → ada yang beli banyak tapi harga gak naik setimpal
    - DISTRIBUTION:  price_change > market_cap_change + 3%  → harga naik tapi market cap gak ikut (pump kecil)
    - ALIGNED_UP:    keduanya naik seiring → trend naik organik
    - ALIGNED_DOWN:  keduanya turun seiring → trend turun organik
    - NEUTRAL:       pergerakan kecil (<1%) atau tidak ada divergensi signifikan
    """
    coin_id = _resolve_coin_id(symbol)
    
    if not coin_id:
        return MarketCapResult(
            coin_id="unknown",
            current_price=0, market_cap=0,
            price_change_24h=0, market_cap_change_24h=0,
            signal="unavailable",
            signal_label="Data N/A",
            signal_emoji="❓",
            interpretation="Market cap data tidak tersedia untuk simbol ini.",
            available=False
        )
    
    cache_key = f"mcap_{coin_id}"
    cached = _get_cached(cache_key)
    
    if cached:
        data = cached
    else:
        try:
            resp = requests.get(
                f"{COINGECKO_BASE}/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false",
                },
                timeout=12
            )
            resp.raise_for_status()
            data = resp.json()
            _set_cache(cache_key, data)
        except Exception as e:
            return MarketCapResult(
                coin_id=coin_id,
                current_price=0, market_cap=0,
                price_change_24h=0, market_cap_change_24h=0,
                signal="error",
                signal_label="API Error",
                signal_emoji="⚠️",
                interpretation=f"Gagal mengambil data market cap: {str(e)}",
                available=False
            )
    
    market_data = data.get("market_data", {})
    current_price = market_data.get("current_price", {}).get("usd", 0.0) or 0.0
    market_cap = market_data.get("market_cap", {}).get("usd", 0.0) or 0.0
    price_change_24h = market_data.get("price_change_percentage_24h", 0.0) or 0.0
    market_cap_change_24h = market_data.get("market_cap_change_percentage_24h", 0.0) or 0.0
    
    # Analisa sinyal divergensi
    divergence = market_cap_change_24h - price_change_24h
    THRESHOLD = 2.5  # % divergensi minimum untuk dianggap sinyal
    
    if abs(price_change_24h) < 0.5 and abs(market_cap_change_24h) < 0.5:
        signal = "neutral"
        signal_label = "Sideways / Konsolidasi"
        signal_emoji = "➡️"
        interpretation = "Harga dan market cap keduanya flat. Pasar sedang konsolidasi."
    elif divergence >= THRESHOLD and market_cap_change_24h > 0:
        signal = "accumulation"
        signal_label = "⚡ AKUMULASI TERDETEKSI"
        signal_emoji = "🟢"
        interpretation = (
            f"Market cap naik **{market_cap_change_24h:+.2f}%** tapi harga hanya **{price_change_24h:+.2f}%**. "
            f"Divergensi **+{divergence:.2f}%** → Ada pihak yang akumulasi diam-diam. "
            f"Harga berpotensi mengikuti market cap dalam beberapa waktu ke depan."
        )
    elif divergence <= -THRESHOLD and price_change_24h > 0:
        signal = "distribution"
        signal_label = "⚠️ DISTRIBUSI / PUMP LEMAH"
        signal_emoji = "🔴"
        interpretation = (
            f"Harga naik **{price_change_24h:+.2f}%** tapi market cap hanya **{market_cap_change_24h:+.2f}%**. "
            f"Divergensi **{divergence:.2f}%** → Pump tanpa dukungan modal kuat. Waspadai reversal."
        )
    elif price_change_24h > 0 and market_cap_change_24h > 0:
        signal = "aligned_up"
        signal_label = "📈 Naik Organik"
        signal_emoji = "🟩"
        interpretation = (
            f"Harga **{price_change_24h:+.2f}%** dan market cap **{market_cap_change_24h:+.2f}%** "
            f"keduanya naik bersamaan. Kenaikan organik dan sehat."
        )
    elif price_change_24h < 0 and market_cap_change_24h < 0:
        signal = "aligned_down"
        signal_label = "📉 Turun Bersamaan"
        signal_emoji = "🟥"
        interpretation = (
            f"Harga **{price_change_24h:+.2f}%** dan market cap **{market_cap_change_24h:+.2f}%** "
            f"keduanya turun. Penjualan terkoordinasi, hindari dulu."
        )
    else:
        signal = "neutral"
        signal_label = "Pergerakan Minor"
        signal_emoji = "⬜"
        interpretation = "Pergerakan terlalu kecil atau tidak ada divergensi signifikan."
    
    return MarketCapResult(
        coin_id=coin_id,
        current_price=current_price,
        market_cap=market_cap,
        price_change_24h=price_change_24h,
        market_cap_change_24h=market_cap_change_24h,
        signal=signal,
        signal_label=signal_label,
        signal_emoji=signal_emoji,
        interpretation=interpretation,
        available=True
    )


def format_market_cap(value: float) -> str:
    """Format angka market cap ke format yang mudah dibaca."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"
