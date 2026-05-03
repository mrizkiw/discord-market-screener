from models.market import StructureResult

def calculate_levels(direction: str, current_price: float, structure: StructureResult):
    sl, tp1, tp2, tp3 = None, None, None, None
    if direction == "bullish":
        sl = structure.latest_swing_low if structure.latest_swing_low else current_price * 0.98
        tp1 = structure.latest_swing_high if structure.latest_swing_high and structure.latest_swing_high > current_price else current_price * 1.02
        tp2 = tp1 + (tp1 - current_price)
        tp3 = tp2 + (tp1 - current_price)
    elif direction == "bearish":
        sl = structure.latest_swing_high if structure.latest_swing_high else current_price * 1.02
        tp1 = structure.latest_swing_low if structure.latest_swing_low and structure.latest_swing_low < current_price else current_price * 0.98
        tp2 = tp1 - (current_price - tp1)
        tp3 = tp2 - (current_price - tp1)
    return sl, tp1, tp2, tp3
