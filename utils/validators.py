def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()

def is_valid_spot_symbol(symbol_info: dict) -> bool:
    if not symbol_info:
        return False
    # Check if it's spot and trading
    if symbol_info.get("status") != "TRADING":
        return False
    
    # Check if spot trading is allowed
    if not symbol_info.get("isSpotTradingAllowed", False):
        return False
        
    return True
