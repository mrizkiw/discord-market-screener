import pandas as pd
from models.market import StructureResult, BreakoutResult, AVPResult, RecommendationResult
from analysis.risk import calculate_levels

def build_recommendation(df: pd.DataFrame, structure: StructureResult, breakout: BreakoutResult, avp: AVPResult) -> RecommendationResult:
    current_price = df.iloc[-1]['close']
    
    status = "Wait"
    entry_text = "No clear entry edge right now."
    confidence = "Low"
    note = "Market is balanced or ranging."
    direction = "neutral"
    
    if structure.trend_label == "HH-HL":
        direction = "bullish"
        if avp.bias == "bullish" and breakout.state == "valid" and breakout.direction == "bullish":
            status = "Buy now"
            entry_text = f"Market is expanding up. Enter near {current_price:.6f}."
            confidence = "High"
            note = "Bullish structure with valid breakout and volume acceptance."
        elif current_price > avp.poc and current_price <= avp.vah:
            status = "Wait for breakout"
            entry_text = f"Wait for price to clear VAH at {avp.vah:.6f}."
            confidence = "Medium"
            note = "Bullish structure but price still inside value area."
        else:
            status = "Buy on retest"
            entry_text = f"Wait for pullback to POC {avp.poc:.6f}."
            confidence = "Medium"
            note = "Price is overextended, wait for retest of value."
            
    elif structure.trend_label == "LH-LL":
        direction = "bearish"
        if avp.bias == "bearish" and breakout.state == "valid" and breakout.direction == "bearish":
            status = "Sell now"
            entry_text = f"Market is expanding down. Enter short near {current_price:.6f}."
            confidence = "High"
            note = "Bearish structure with valid breakdown and volume acceptance."
        elif current_price < avp.poc and current_price >= avp.val:
            status = "Wait for breakdown"
            entry_text = f"Wait for price to clear VAL at {avp.val:.6f}."
            confidence = "Medium"
            note = "Bearish structure but price still inside value area."
        else:
            status = "Sell on retest"
            entry_text = f"Wait for pullback to POC {avp.poc:.6f}."
            confidence = "Medium"
            note = "Price is overextended downwards, wait for retest."
            
    sl, tp1, tp2, tp3 = calculate_levels(direction, current_price, structure)
    
    if status == "Wait":
        sl, tp1, tp2, tp3 = None, None, None, None
        
    return RecommendationResult(status, entry_text, sl, tp1, tp2, tp3, confidence, note)
