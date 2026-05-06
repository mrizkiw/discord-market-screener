import pandas as pd
from models.market import StructureResult, BreakoutResult, AVPResult, RecommendationResult
from analysis.risk import calculate_levels

def build_recommendation(df: pd.DataFrame, structure: StructureResult, breakout: BreakoutResult, avp: AVPResult) -> RecommendationResult:
    current_price = df.iloc[-1]['close']
    
    status = "Wait"
    entry_text = "**Entry:** No clear entry edge right now.\n**Strategy:** Do nothing until a clear setup forms."
    confidence = "Low"
    note = "Market is balanced or ranging."
    direction = "neutral"
    
    if structure.trend_label == "HH-HL":
        direction = "bullish"
        sh = structure.latest_swing_high if structure.latest_swing_high else current_price
        
        if avp.bias == "bullish" and breakout.state == "valid" and breakout.direction == "bullish":
            status = "Buy now"
            entry_text = f"**Entry Zone:** `{sh:.8f}` (Retest) to `{current_price:.8f}` (Current)\n**Strategy:** Enter partial now, add more if price retests the breakout level."
            confidence = "High"
            note = "Bullish structure with valid breakout and volume acceptance."
        elif current_price > avp.poc and current_price <= avp.vah:
            status = "Wait for breakout"
            entry_text = f"**Trigger:** Wait for candle to close above VAH (`{avp.vah:.8f}`).\n**Strategy:** Do not enter yet, wait for confirmation."
            confidence = "Medium"
            note = "Bullish structure but price still inside value area."
        else:
            status = "Buy on retest"
            entry_text = f"**Entry Zone:** `{avp.poc:.8f}` (POC) to `{avp.vah:.8f}` (VAH)\n**Strategy:** Price is overextended. Wait for a pullback to value area."
            confidence = "Medium"
            note = "Price is overextended, wait for retest of value."
            
    elif structure.trend_label == "LH-LL":
        direction = "bearish"
        status = "Avoid (Downtrend)"
        entry_text = "**Warning:** Market is in a downtrend.\n**Strategy:** Spot market only. Do not buy until structure reverses."
        confidence = "High"
        note = "Bearish structure. No shorting in Spot."
            
    elif structure.trend_label == "range":
        if breakout.state == "valid" and breakout.direction == "bearish":
            status = "Avoid (Breakdown)"
            entry_text = "**Warning:** Market is breaking down from the range.\n**Strategy:** Spot market only. Do not buy until structure reverses."
            confidence = "High"
            note = "Valid bearish breakdown out of range."
            direction = "neutral"
        elif breakout.state == "valid" and breakout.direction == "bullish":
            status = "Buy Breakout"
            sh = structure.latest_swing_high if structure.latest_swing_high else current_price
            entry_text = f"**Entry Zone:** `{sh:.8f}` (Retest) to `{current_price:.8f}` (Current)\n**Strategy:** Enter partial now, range is breaking up."
            confidence = "High"
            note = "Valid bullish breakout out of range."
            direction = "bullish"
        elif avp.val and current_price <= avp.val * 1.01:
            status = "Buy range low"
            entry_text = f"**Entry Zone:** `{avp.val:.8f}` (VAL) to `{current_price:.8f}` (Current)\n**Strategy:** Fading the range. Buy near the bottom support."
            confidence = "Medium"
            note = "Fading the range low."
            direction = "range_bullish"
        elif avp.vah and current_price >= avp.vah * 0.99:
            status = "Avoid (Range High)"
            entry_text = f"**Warning:** Price is at range resistance (`{avp.vah:.8f}`).\n**Strategy:** Spot market only. Do not buy here. Wait for breakout or pullback."
            confidence = "Medium"
            note = "Price is at range high."
            direction = "neutral"
            
    if direction in ["bullish", "bearish"]:
        sl, tp1, tp2, tp3 = calculate_levels(direction, current_price, structure)
    elif direction == "range_bullish":
        sl = structure.latest_swing_low if structure.latest_swing_low else current_price * 0.98
        tp1, tp2, tp3 = avp.poc, avp.vah, structure.latest_swing_high
    else:
        sl, tp1, tp2, tp3 = None, None, None, None
    
    if "Wait" in status or "Avoid" in status:
        sl, tp1, tp2, tp3 = None, None, None, None
        
    return RecommendationResult(status, entry_text, sl, tp1, tp2, tp3, confidence, note)
