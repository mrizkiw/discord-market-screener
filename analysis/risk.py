from models.market import StructureResult

def calculate_levels(direction: str, current_price: float, structure: StructureResult):
    sl, tp1, tp2, tp3 = None, None, None, None
    
    if direction == "bullish":
        sl = structure.latest_swing_low if structure.latest_swing_low else current_price * 0.98
        
        if structure.latest_swing_high and structure.latest_swing_low:
            swing_range = structure.latest_swing_high - structure.latest_swing_low
            tp1 = structure.latest_swing_low + (swing_range * 1.272)
            tp2 = structure.latest_swing_low + (swing_range * 1.618)
            tp3 = structure.latest_swing_low + (swing_range * 2.618)
            
            # Make sure TP1 is actually above the current price
            if tp1 <= current_price:
                tp1 = structure.latest_swing_low + (swing_range * 1.618)
                tp2 = structure.latest_swing_low + (swing_range * 2.618)
                tp3 = structure.latest_swing_low + (swing_range * 3.618)
        else:
            tp1 = current_price * 1.02
            tp2 = current_price * 1.04
            tp3 = current_price * 1.06
            
    elif direction == "bearish":
        sl = structure.latest_swing_high if structure.latest_swing_high else current_price * 1.02
        
        if structure.latest_swing_high and structure.latest_swing_low:
            swing_range = structure.latest_swing_high - structure.latest_swing_low
            tp1 = structure.latest_swing_high - (swing_range * 1.272)
            tp2 = structure.latest_swing_high - (swing_range * 1.618)
            tp3 = structure.latest_swing_high - (swing_range * 2.618)
            
            # Make sure TP1 is actually below the current price
            if tp1 >= current_price:
                tp1 = structure.latest_swing_high - (swing_range * 1.618)
                tp2 = structure.latest_swing_high - (swing_range * 2.618)
                tp3 = structure.latest_swing_high - (swing_range * 3.618)
        else:
            tp1 = current_price * 0.98
            tp2 = current_price * 0.96
            tp3 = current_price * 0.94
            
    return sl, tp1, tp2, tp3
