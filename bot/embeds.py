import discord
import datetime
from models.market import StructureResult, BreakoutResult, AVPResult, RecommendationResult, MTFResult, MarketCapResult

def build_basic_response(symbol: str, price: float, candle_count: int, interval: str,
                         structure: StructureResult = None, breakout: BreakoutResult = None,
                         avp: AVPResult = None, recommendation: RecommendationResult = None,
                         mtf: MTFResult = None, marketcap: MarketCapResult = None) -> discord.Embed:
    
    status_text = recommendation.status if recommendation else "Active Analysis"
    color = discord.Color.blue()
    if recommendation:
        if "Buy" in recommendation.status: color = discord.Color.green()
        elif "Watch" in recommendation.status: color = discord.Color.orange()
        elif "Avoid" in recommendation.status: color = discord.Color.red()
        elif "Sell" in recommendation.status: color = discord.Color.red()
        
    embed = discord.Embed(
        title=f"{symbol} - {interval}",
        description=f"Status: **{status_text}**",
        color=color
    )
    
    if structure:
        embed.add_field(name="Trend", value=structure.trend_label, inline=True)
        sh_val = f"{structure.latest_swing_high:.8f}" if structure.latest_swing_high else "N/A"
        sl_val = f"{structure.latest_swing_low:.8f}" if structure.latest_swing_low else "N/A"
        embed.add_field(name="Swing High", value=sh_val, inline=True)
        embed.add_field(name="Swing Low", value=sl_val, inline=True)
        
    if breakout and breakout.state != "no_breakout":
        embed.add_field(name="Breakout", value=f"{breakout.state.title()} {breakout.direction} at {breakout.level:.8f}", inline=False)
        
    if avp:
        embed.add_field(name="AVP Bias", value=avp.bias.title(), inline=True)
        embed.add_field(name="POC", value=f"{avp.poc:.8f}", inline=True)
        embed.add_field(name="VAH / VAL", value=f"{avp.vah:.8f} / {avp.val:.8f}", inline=True)
        
    if recommendation:
        embed.add_field(name=f"⚡ ACTION: {recommendation.status.upper()}", value=recommendation.entry_text, inline=False)
        embed.add_field(name="Confidence", value=recommendation.confidence, inline=True)
        embed.add_field(name="Notes", value=recommendation.note, inline=True)
        
        if recommendation.sl:
            def calc_pct(target):
                return f"{((target - price) / price) * 100:+.2f}%"
                
            sl_pct = calc_pct(recommendation.sl)
            embed.add_field(name="🛑 Stop Loss", value=f"`{recommendation.sl:.8f}` ({sl_pct})", inline=True)
            
            tp_parts = []
            if recommendation.tp1: tp_parts.append(f"TP1: `{recommendation.tp1:.8f}` ({calc_pct(recommendation.tp1)})")
            if recommendation.tp2: tp_parts.append(f"TP2: `{recommendation.tp2:.8f}` ({calc_pct(recommendation.tp2)})")
            if recommendation.tp3: tp_parts.append(f"TP3: `{recommendation.tp3:.8f}` ({calc_pct(recommendation.tp3)})")
            if tp_parts:
                embed.add_field(name="🎯 Take Profit", value="\n".join(tp_parts), inline=True)
    if mtf and mtf.macro_tf != "None":
        embed.add_field(name="MTF Confluence", value=f"**{mtf.confluence}**\nMacro ({mtf.macro_tf}): {mtf.macro_trend} / {mtf.macro_bias.title()}\nMicro ({mtf.micro_tf}): {mtf.micro_trend} / {mtf.micro_bias.title()}", inline=False)

    # Market Cap Section
    if marketcap and marketcap.available:
        from analysis.marketcap import format_market_cap
        mcap_str = format_market_cap(marketcap.market_cap)
        price_chg = f"{marketcap.price_change_24h:+.2f}%"
        mcap_chg = f"{marketcap.market_cap_change_24h:+.2f}%"
        divergence = marketcap.market_cap_change_24h - marketcap.price_change_24h
        div_str = f"{divergence:+.2f}%"

        embed.add_field(
            name=f"{marketcap.signal_emoji} Market Cap — {marketcap.signal_label}",
            value=(
                f"**Market Cap:** {mcap_str}\n"
                f"**Harga 24h:** {price_chg} | **MCap 24h:** {mcap_chg} | **Divergensi:** {div_str}\n"
                f"*{marketcap.interpretation}*"
            ),
            inline=False
        )
    elif marketcap and not marketcap.available:
        embed.add_field(name="❓ Market Cap", value=marketcap.interpretation, inline=False)
        
    embed.add_field(name="Last Price", value=f"{price:.8f}", inline=False)
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed

def build_error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="Error",
        description=message,
        color=discord.Color.red()
    )
