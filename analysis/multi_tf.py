from models.market import MTFResult
from analysis.structure import get_market_structure
from analysis.avp import calculate_avp
from utils.timeframes import get_mtf_mapping

def analyze_mtf(symbol: str, main_tf: str, market_service) -> MTFResult:
    macro_tf, micro_tf = get_mtf_mapping(main_tf)
    
    macro_trend = "N/A"
    macro_bias = "N/A"
    if macro_tf:
        try:
            macro_df = market_service.fetch_candles(symbol, macro_tf, 100)
            if not macro_df.empty:
                s = get_market_structure(macro_df)
                a = calculate_avp(macro_df, s)
                macro_trend = s.trend_label
                macro_bias = a.bias
        except Exception:
            pass
            
    micro_trend = "N/A"
    micro_bias = "N/A"
    if micro_tf:
        try:
            micro_df = market_service.fetch_candles(symbol, micro_tf, 100)
            if not micro_df.empty:
                s = get_market_structure(micro_df)
                a = calculate_avp(micro_df, s)
                micro_trend = s.trend_label
                micro_bias = a.bias
        except Exception:
            pass
            
    # confluence logic
    confluence = "Mixed / Unclear"
    if macro_trend == "HH-HL" and macro_bias == "bullish":
        if micro_trend == "HH-HL" and micro_bias == "bullish":
            confluence = "Strong Bullish (Aligned)"
        elif micro_trend == "LH-LL" and micro_bias == "bearish":
            confluence = "Bullish Macro, Micro Pullback"
        else:
            confluence = "Bullish Macro, Micro Ranging"
            
    elif macro_trend == "LH-LL" and macro_bias == "bearish":
        if micro_trend == "LH-LL" and micro_bias == "bearish":
            confluence = "Strong Bearish (Aligned)"
        elif micro_trend == "HH-HL" and micro_bias == "bullish":
            confluence = "Bearish Macro, Micro Rally"
        else:
            confluence = "Bearish Macro, Micro Ranging"

    return MTFResult(macro_tf or "None", macro_trend, macro_bias, micro_tf or "None", micro_trend, micro_bias, confluence)
