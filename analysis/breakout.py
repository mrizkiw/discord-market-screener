import pandas as pd
from models.market import StructureResult, BreakoutResult

def detect_breakout(df: pd.DataFrame, structure: StructureResult, vol_multiplier: float = 1.2) -> BreakoutResult:
    if len(df) < 21:
        return BreakoutResult("no_breakout", None, None)
        
    # Average volume of the previous 20 candles
    avg_vol = df['volume'].iloc[-21:-1].mean()
    
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]
    
    latest_sh = structure.latest_swing_high
    latest_sl = structure.latest_swing_low
    
    # Check bullish breakout
    if latest_sh:
        # Failed breakout: prev candle closed above, but current closed below
        if prev_candle['close'] > latest_sh and last_candle['close'] <= latest_sh:
            return BreakoutResult("failed", latest_sh, "bullish")
            
        if last_candle['close'] > latest_sh:
            # Volume confirmation
            if last_candle['volume'] > avg_vol * vol_multiplier:
                return BreakoutResult("valid", latest_sh, "bullish")
            else:
                return BreakoutResult("weak", latest_sh, "bullish")
                
        elif last_candle['high'] > latest_sh and last_candle['close'] <= latest_sh:
            return BreakoutResult("weak", latest_sh, "bullish")
            
    # Check bearish breakout
    if latest_sl:
        # Failed breakdown: prev candle closed below, but current closed above
        if prev_candle['close'] < latest_sl and last_candle['close'] >= latest_sl:
            return BreakoutResult("failed", latest_sl, "bearish")
            
        if last_candle['close'] < latest_sl:
            # Volume confirmation
            if last_candle['volume'] > avg_vol * vol_multiplier:
                return BreakoutResult("valid", latest_sl, "bearish")
            else:
                return BreakoutResult("weak", latest_sl, "bearish")
                
        elif last_candle['low'] < latest_sl and last_candle['close'] >= latest_sl:
            return BreakoutResult("weak", latest_sl, "bearish")
            
    return BreakoutResult("no_breakout", None, None)
