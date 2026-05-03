import pandas as pd
from models.market import StructureResult, BreakoutResult

def detect_breakout(df: pd.DataFrame, structure: StructureResult) -> BreakoutResult:
    if len(df) < 2:
        return BreakoutResult("no_breakout", None, None)
        
    last_candle = df.iloc[-1]
    
    latest_sh = structure.latest_swing_high
    latest_sl = structure.latest_swing_low
    
    # Check bullish breakout
    if latest_sh:
        if last_candle['close'] > latest_sh:
            return BreakoutResult("valid", latest_sh, "bullish")
        elif last_candle['high'] > latest_sh and last_candle['close'] <= latest_sh:
            return BreakoutResult("weak", latest_sh, "bullish")
            
    # Check bearish breakout
    if latest_sl:
        if last_candle['close'] < latest_sl:
            return BreakoutResult("valid", latest_sl, "bearish")
        elif last_candle['low'] < latest_sl and last_candle['close'] >= latest_sl:
            return BreakoutResult("weak", latest_sl, "bearish")
            
    return BreakoutResult("no_breakout", None, None)
