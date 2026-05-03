import discord
from discord.ext import tasks, commands
from services.watchlist import WatchlistService
from services.market_data import MarketDataService
from analysis.structure import get_market_structure
from analysis.breakout import detect_breakout
from analysis.avp import calculate_avp
from analysis.recommendation import build_recommendation
from analysis.multi_tf import analyze_mtf
from bot.embeds import build_basic_response
from config import DEFAULT_TIMEFRAME

class AlertTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.watchlist = WatchlistService()
        self.market_service = MarketDataService()
        self.last_alerts = {}
        self.alert_loop.start()

    def cog_unload(self):
        self.alert_loop.cancel()

    @tasks.loop(minutes=5)
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
                    if cache_key in self.last_alerts:
                        continue
                        
                    self.last_alerts[cache_key] = True
                    
                    rec = build_recommendation(df, structure, breakout, avp)
                    mtf = analyze_mtf(symbol, DEFAULT_TIMEFRAME, self.market_service)
                    
                    embed = build_basic_response(symbol, last_price, len(df), DEFAULT_TIMEFRAME, structure, breakout, avp, rec, mtf)
                    embed.title = f"🚨 CONFIRMED ALERT: {symbol} Breakout! 🚨"
                    
                    for u in users:
                        channel = self.bot.get_channel(int(u['channel_id']))
                        if channel:
                            await channel.send(content=f"<@{u['user_id']}> Confirmed breakout detected for {symbol}!", embed=embed)
                            
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
                        if cache_key not in self.last_alerts:
                            self.last_alerts[cache_key] = True
                            
                            rec = build_recommendation(df, structure, breakout, avp)
                            mtf = analyze_mtf(symbol, DEFAULT_TIMEFRAME, self.market_service)
                            
                            embed = build_basic_response(symbol, last_price, len(df), DEFAULT_TIMEFRAME, structure, breakout, avp, rec, mtf)
                            embed.title = f"🟡 EARLY WARNING: {symbol} 🟡"
                            embed.description = f"**{early_reason}** at `{early_level:.6f}`. Get ready!"
                            
                            for u in users:
                                channel = self.bot.get_channel(int(u['channel_id']))
                                if channel:
                                    await channel.send(content=f"<@{u['user_id']}> {symbol} is making a move!", embed=embed)
                                    
            except Exception as e:
                print(f"Alert loop error on {symbol}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AlertTasks(bot))
