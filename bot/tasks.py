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
                
                if breakout.state == "valid":
                    cache_key = f"{symbol}_{breakout.level}"
                    if cache_key in self.last_alerts:
                        continue
                        
                    self.last_alerts[cache_key] = True
                    
                    avp = calculate_avp(df, structure)
                    rec = build_recommendation(df, structure, breakout, avp)
                    mtf = analyze_mtf(symbol, DEFAULT_TIMEFRAME, self.market_service)
                    
                    last_price = float(df.iloc[-1]["close"])
                    
                    embed = build_basic_response(symbol, last_price, len(df), DEFAULT_TIMEFRAME, structure, breakout, avp, rec, mtf)
                    embed.title = f"🚨 ALERT: {symbol} Breakout! 🚨"
                    
                    for u in users:
                        channel = self.bot.get_channel(int(u['channel_id']))
                        if channel:
                            await channel.send(content=f"<@{u['user_id']}> Breakout detected for {symbol}!", embed=embed)
                            
            except Exception as e:
                print(f"Alert loop error on {symbol}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AlertTasks(bot))
