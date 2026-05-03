import discord
from models.market import StructureResult, BreakoutResult, AVPResult, RecommendationResult, MTFResult

def build_basic_response(symbol: str, price: float, candle_count: int, interval: str,
                         structure: StructureResult = None, breakout: BreakoutResult = None,
                         avp: AVPResult = None, recommendation: RecommendationResult = None,
                         mtf: MTFResult = None) -> discord.Embed:
    
    status_text = recommendation.status if recommendation else "Active Analysis"
    color = discord.Color.blue()
    if recommendation:
        if "Buy" in recommendation.status: color = discord.Color.green()
        elif "Sell" in recommendation.status: color = discord.Color.red()
        
    embed = discord.Embed(
        title=f"{symbol} - {interval}",
        description=f"Status: **{status_text}**",
        color=color
    )
    
    if structure:
        embed.add_field(name="Trend", value=structure.trend_label, inline=True)
        sh_val = f"{structure.latest_swing_high:.6f}" if structure.latest_swing_high else "N/A"
        sl_val = f"{structure.latest_swing_low:.6f}" if structure.latest_swing_low else "N/A"
        embed.add_field(name="Swing High", value=sh_val, inline=True)
        embed.add_field(name="Swing Low", value=sl_val, inline=True)
        
    if breakout and breakout.state != "no_breakout":
        embed.add_field(name="Breakout", value=f"{breakout.state.title()} {breakout.direction} at {breakout.level:.6f}", inline=False)
        
    if avp:
        embed.add_field(name="AVP Bias", value=avp.bias.title(), inline=True)
        embed.add_field(name="POC", value=f"{avp.poc:.6f}", inline=True)
        embed.add_field(name="VAH / VAL", value=f"{avp.vah:.6f} / {avp.val:.6f}", inline=True)
        
    if recommendation:
        embed.add_field(name="Recommendation", value=f"**{recommendation.status}**: {recommendation.entry_text}", inline=False)
        embed.add_field(name="Confidence", value=recommendation.confidence, inline=True)
        embed.add_field(name="Notes", value=recommendation.note, inline=True)
        
        if recommendation.sl:
            tp_str = f"TP1: {recommendation.tp1:.6f}" if recommendation.tp1 else ""
            if recommendation.tp2: tp_str += f" | TP2: {recommendation.tp2:.6f}"
            if recommendation.tp3: tp_str += f" | TP3: {recommendation.tp3:.6f}"
            embed.add_field(name="Targets", value=f"SL: {recommendation.sl:.6f}\n{tp_str}", inline=False)
    if mtf and mtf.macro_tf != "None":
        embed.add_field(name="MTF Confluence", value=f"**{mtf.confluence}**\nMacro ({mtf.macro_tf}): {mtf.macro_trend} / {mtf.macro_bias.title()}\nMicro ({mtf.micro_tf}): {mtf.micro_trend} / {mtf.micro_bias.title()}", inline=False)
        
    embed.add_field(name="Last Price", value=f"{price:.6f}", inline=False)
    return embed

def build_error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="Error",
        description=message,
        color=discord.Color.red()
    )
