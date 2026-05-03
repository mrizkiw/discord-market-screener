import pandas as pd
from models.market import StructureResult

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr0 = abs(df['high'] - df['low'])
    tr1 = abs(df['high'] - df['close'].shift())
    tr2 = abs(df['low'] - df['close'].shift())
    tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_market_structure(df: pd.DataFrame, n: int = 3, atr_multiplier: float = 0.5) -> StructureResult:
    if len(df) < n * 2 + 1:
        return StructureResult(None, None, None, None, "insufficient_data")
        
    df = df.copy()
    df['atr'] = calculate_atr(df)
    
    swing_highs = []
    swing_lows = []
    
    for i in range(n, len(df) - n):
        # Swing High
        if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, n+1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, n+1)):
            
            # Distance filter
            if not swing_highs or (df['high'].iloc[i] > swing_highs[-1][1] or abs(df['high'].iloc[i] - swing_highs[-1][1]) > df['atr'].iloc[i] * atr_multiplier):
                swing_highs.append((i, df['high'].iloc[i]))
                
        # Swing Low
        if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, n+1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, n+1)):
            
            if not swing_lows or (df['low'].iloc[i] < swing_lows[-1][1] or abs(df['low'].iloc[i] - swing_lows[-1][1]) > df['atr'].iloc[i] * atr_multiplier):
                swing_lows.append((i, df['low'].iloc[i]))

    latest_sh = swing_highs[-1][1] if swing_highs else None
    prev_sh = swing_highs[-2][1] if len(swing_highs) > 1 else None
    
    latest_sl = swing_lows[-1][1] if swing_lows else None
    prev_sl = swing_lows[-2][1] if len(swing_lows) > 1 else None
    
    trend = "range"
    if latest_sh and prev_sh and latest_sl and prev_sl:
        if latest_sh > prev_sh and latest_sl > prev_sl:
            trend = "HH-HL"
        elif latest_sh < prev_sh and latest_sl < prev_sl:
            trend = "LH-LL"
        else:
            trend = "range"
            
    return StructureResult(latest_sh, latest_sl, prev_sh, prev_sl, trend)
