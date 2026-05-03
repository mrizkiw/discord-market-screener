import pandas as pd
import numpy as np
from models.market import StructureResult, AVPResult

def calculate_avp(df: pd.DataFrame, structure: StructureResult) -> AVPResult:
    if len(df) < 10:
        return AVPResult(0, 0.0, 0.0, 0.0, "neutral")

    anchor_idx = 0
    if structure.trend_label == "HH-HL" and structure.latest_swing_low:
        anchor_rows = df[df['low'] == structure.latest_swing_low]
        if not anchor_rows.empty:
            anchor_idx = anchor_rows.index[-1]
    elif structure.trend_label == "LH-LL" and structure.latest_swing_high:
        anchor_rows = df[df['high'] == structure.latest_swing_high]
        if not anchor_rows.empty:
            anchor_idx = anchor_rows.index[-1]
    else:
        anchor_idx = max(0, len(df) - 30)

    profile_df = df.iloc[anchor_idx:]
    if profile_df.empty:
        return AVPResult(anchor_idx, 0.0, 0.0, 0.0, "neutral")

    min_price = profile_df['low'].min()
    max_price = profile_df['high'].max()
    
    if min_price == max_price:
        return AVPResult(anchor_idx, min_price, max_price, min_price, "neutral")
        
    bins = np.linspace(min_price, max_price, 50)
    vol_profile = np.zeros(len(bins) - 1)
    
    for _, row in profile_df.iterrows():
        low_idx = np.searchsorted(bins, row['low']) - 1
        high_idx = np.searchsorted(bins, row['high'])
        
        low_idx = max(0, low_idx)
        high_idx = min(len(bins)-1, high_idx)
        
        if high_idx > low_idx:
            vol_per_bin = row['volume'] / (high_idx - low_idx)
            vol_profile[low_idx:high_idx] += vol_per_bin
        else:
            idx = max(0, min(len(bins)-2, low_idx))
            vol_profile[idx] += row['volume']
            
    poc_idx = np.argmax(vol_profile)
    poc = (bins[poc_idx] + bins[poc_idx+1]) / 2
    
    total_vol = np.sum(vol_profile)
    target_vol = total_vol * 0.7
    
    current_vol = vol_profile[poc_idx]
    low_i = poc_idx - 1
    high_i = poc_idx + 1
    
    while current_vol < target_vol and (low_i >= 0 or high_i < len(vol_profile)):
        vol_low = vol_profile[low_i] if low_i >= 0 else 0
        vol_high = vol_profile[high_i] if high_i < len(vol_profile) else 0
        
        if vol_low >= vol_high and low_i >= 0:
            current_vol += vol_low
            low_i -= 1
        elif high_i < len(vol_profile):
            current_vol += vol_high
            high_i += 1
        else:
            if low_i >= 0:
                current_vol += vol_profile[low_i]
                low_i -= 1
                
    val = bins[max(0, low_i + 1)]
    vah = bins[min(len(bins)-1, high_i)]
    
    last_close = df.iloc[-1]['close']
    if last_close > vah:
        bias = "bullish"
    elif last_close < val:
        bias = "bearish"
    else:
        bias = "neutral"
        
    return AVPResult(anchor_idx, poc, vah, val, bias)
