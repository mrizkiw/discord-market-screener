import discord
import datetime
import time
from discord.ext import tasks, commands
from services.watchlist import WatchlistService
from services.market_data import MarketDataService
from analysis.structure import get_market_structure
from analysis.breakout import detect_breakout
from analysis.avp import calculate_avp
from analysis.recommendation import build_recommendation
from analysis.multi_tf import analyze_mtf
from analysis.charting import generate_chart
from bot.embeds import build_basic_response
from config import DEFAULT_TIMEFRAME

ALERT_CACHE_TTL = 3600  # 1 hour - alerts expire after this

class AlertTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.watchlist = WatchlistService()
        self.market_service = MarketDataService()
        self.last_alerts = {}  # {cache_key: timestamp}
        self.alert_loop.start()
        self.daily_scanner_loop.start()
        self.picks_tracker_loop.start()
    
    def _is_alert_cached(self, cache_key: str) -> bool:
        """Check if alert is cached and not expired."""
        if cache_key not in self.last_alerts:
            return False
        elapsed = time.time() - self.last_alerts[cache_key]
        if elapsed > ALERT_CACHE_TTL:
            del self.last_alerts[cache_key]
            return False
        return True
    
    def _cache_alert(self, cache_key: str):
        """Cache alert with current timestamp."""
        # Cleanup expired entries periodically
        now = time.time()
        expired = [k for k, v in self.last_alerts.items() if now - v > ALERT_CACHE_TTL]
        for k in expired:
            del self.last_alerts[k]
        self.last_alerts[cache_key] = now

    def cog_unload(self):
        self.alert_loop.cancel()
        self.daily_scanner_loop.cancel()
        self.picks_tracker_loop.cancel()

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc))
    async def daily_scanner_loop(self):
        await self.bot.wait_until_ready()
        from services.scanner import ScannerService
        scanner = ScannerService()
        scanner.refresh_daily_picks()
        symbols = scanner.get_daily_picks()
        
        if not symbols:
            return
            
        targets = self.watchlist.get_all_targets()
        channels = set()
        for users in targets.values():
            for u in users:
                channels.add(int(u['channel_id']))
                
        if channels:
            embed = discord.Embed(
                title="🌟 Daily Top Volume Movers 🌟",
                description="Top 5 spot coins moving today with strong liquidity (3-30% gain, >$10M volume).",
                color=discord.Color.purple()
            )
            embed.add_field(name="Top Picks", value="\n".join(f"• **{s}**" for s in symbols), inline=False)
            embed.set_footer(text="Add these to your watchlist with /wl_add if you spot a good setup!")
            
            for ch_id in channels:
                channel = self.bot.get_channel(ch_id)
                if channel:
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Failed to send daily picks to {ch_id}: {e}")

    @tasks.loop(time=[datetime.time(hour=h, minute=m, tzinfo=datetime.timezone.utc) for h in range(24) for m in (0, 30)])
    async def picks_tracker_loop(self):
        await self.bot.wait_until_ready()
        import asyncio
        await asyncio.sleep(5) # Wait 5 seconds to ensure Binance candles have rolled over
        
        from services.scanner import ScannerService
        scanner = ScannerService()
        symbols = scanner.get_daily_picks()
        if not symbols: return
        
        targets = self.watchlist.get_all_targets()
        channels = set()
        for users in targets.values():
            for u in users:
                channels.add(int(u['channel_id']))
        if not channels: return
        
        embed = discord.Embed(
            title="📊 Daily Picks Performance",
            description="Tracking profit/loss of today's top picks.\n`Daily`: Since 00:00 UTC | `Last 30m`: Previous 30m candle.",
            color=discord.Color.blue()
        )
        
        perf_text = []
        for sym in symbols:
            try:
                # 1. Fetch Daily Performance
                df_1d = self.market_service.fetch_candles(sym, "1d", 2)
                pct_daily = 0.0
                current_price = 0.0
                if not df_1d.empty:
                    today_candle = df_1d.iloc[-1]
                    open_daily = float(today_candle["open"])
                    current_price = float(today_candle["close"])
                    if open_daily > 0:
                        pct_daily = ((current_price - open_daily) / open_daily) * 100
                        
                # 2. Fetch 30m Performance
                df_30m = self.market_service.fetch_candles(sym, "30m", 2)
                pct_30m = 0.0
                if not df_30m.empty and len(df_30m) >= 2:
                    closed_30m = df_30m.iloc[-2]
                    open_30m = float(closed_30m["open"])
                    close_30m = float(closed_30m["close"])
                    if open_30m > 0:
                        pct_30m = ((close_30m - open_30m) / open_30m) * 100
                        
                emoji = "🟢" if pct_daily >= 0 else "🔴"
                perf_text.append(f"{emoji} **{sym}**: `{current_price:.8f}`\n└ Daily: **{pct_daily:+.2f}%** | Last 30m: **{pct_30m:+.2f}%**")
            except Exception as e:
                print(f"Error fetching perf for {sym}: {e}")
                
        if perf_text:
            embed.description += "\n\n" + "\n".join(perf_text)
            for ch_id in channels:
                channel = self.bot.get_channel(ch_id)
                if channel:
                    try:
                        await channel.send(embed=embed)
                    except Exception as e:
                        pass

    @tasks.loop(minutes=2)
    async def alert_loop(self):
        await self.bot.wait_until_ready()
        
        targets = self.watchlist.get_all_targets()
        if not targets:
            return
            
        for symbol, users in targets.items():
            try:
                df = self.market_service.fetch_candles(symbol, DEFAULT_TIMEFRAME, 100)
                if df.empty: continue
                
                structure = get_market_structure(df)
                breakout = detect_breakout(df, structure)
                avp = calculate_avp(df, structure)
                
                last_price = float(df.iloc[-1]["close"])
                
                if breakout.state == "valid":
                    cache_key = f"{symbol}_{breakout.level}_confirmed"
                    if self._is_alert_cached(cache_key):
                        continue
                        
                    self._cache_alert(cache_key)
                    
                    rec = build_recommendation(df, structure, breakout, avp)
                    mtf = analyze_mtf(symbol, DEFAULT_TIMEFRAME, self.market_service)
                    
                    embed = build_basic_response(symbol, last_price, len(df), DEFAULT_TIMEFRAME, structure, breakout, avp, rec, mtf)
                    
                    is_bearish = breakout.direction == "bearish" or "Avoid" in rec.status
                    embed.title = f"🚨 DANGER: {symbol} Breakdown! 🚨" if is_bearish else f"🚨 CONFIRMED ALERT: {symbol} Breakout! 🚨"
                    
                    try:
                        chart_buf = generate_chart(symbol, df, structure, avp)
                        chart_file = discord.File(chart_buf, filename="chart.png")
                        embed.set_image(url="attachment://chart.png")
                    except Exception:
                        chart_file = None
                    
                    for u in users:
                        channel = self.bot.get_channel(int(u['channel_id']))
                        if channel:
                            msg = f"<@{u['user_id']}> Warning: Bearish breakdown for {symbol}!" if is_bearish else f"<@{u['user_id']}> Confirmed breakout detected for {symbol}!"
                            if chart_file:
                                chart_buf.seek(0)
                                chart_file = discord.File(chart_buf, filename="chart.png")
                            await channel.send(content=msg, embed=embed, file=chart_file)
                            
                else:
                    # Early Warning Logic
                    is_early = False
                    early_reason = ""
                    early_level = 0.0
                    
                    sh = structure.latest_swing_high
                    sl = structure.latest_swing_low
                    
                    if sh and (sh * 0.99) <= last_price < sh:
                        is_early, early_reason, early_level = True, "Approaching Swing High", sh
                    elif avp.vah and (avp.vah * 0.99) <= last_price < avp.vah:
                        is_early, early_reason, early_level = True, "Approaching VAH", avp.vah
                    elif sl and (sl * 1.01) >= last_price > sl:
                        is_early, early_reason, early_level = True, "Approaching Swing Low", sl
                    elif avp.val and (avp.val * 1.01) >= last_price > avp.val:
                        is_early, early_reason, early_level = True, "Approaching VAL", avp.val
                        
                    if is_early:
                        cache_key = f"{symbol}_{early_level}_early"
                        if not self._is_alert_cached(cache_key):
                            self._cache_alert(cache_key)
                            
                            rec = build_recommendation(df, structure, breakout, avp)
                            
                            # Skip spammy early warnings if the recommendation is to Avoid anyway
                            if "Avoid" in rec.status:
                                continue
                                
                            mtf = analyze_mtf(symbol, DEFAULT_TIMEFRAME, self.market_service)
                            
                            embed = build_basic_response(symbol, last_price, len(df), DEFAULT_TIMEFRAME, structure, breakout, avp, rec, mtf)
                            embed.title = f"🟡 EARLY WARNING: {symbol} 🟡"
                            embed.description = f"**{early_reason}** at `{early_level:.8f}`. Get ready!"
                            
                            try:
                                chart_buf = generate_chart(symbol, df, structure, avp)
                                chart_file = discord.File(chart_buf, filename="chart.png")
                                embed.set_image(url="attachment://chart.png")
                            except Exception:
                                chart_file = None
                            
                            for u in users:
                                channel = self.bot.get_channel(int(u['channel_id']))
                                if channel:
                                    if chart_file:
                                        chart_buf.seek(0)
                                        chart_file = discord.File(chart_buf, filename="chart.png")
                                    await channel.send(content=f"<@{u['user_id']}> {symbol} is making a move!", embed=embed, file=chart_file)
                                    
            except discord.Forbidden as e:
                print(f"[PERMISSION ERROR] Bot missing permissions for {symbol}. Check bot role in that channel. ({e})")
            except Exception as e:
                print(f"Alert loop error on {symbol}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AlertTasks(bot))
