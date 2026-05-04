import discord
from discord import app_commands
from discord.ext import commands
from utils.validators import normalize_symbol, is_valid_spot_symbol
from services.market_data import MarketDataService
from bot.embeds import build_basic_response, build_error_embed
from config import DEFAULT_TIMEFRAME, DEFAULT_CANDLE_LIMIT

class MonitorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.market_service = MarketDataService()

    async def symbol_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            info = self.market_service.client.get_exchange_info()
            symbols = [s['symbol'] for s in info.get("symbols", []) if is_valid_spot_symbol(s)]
        except Exception:
            return []
            
        current = current.upper()
        matches = [s for s in symbols if current in s]
        matches.sort(key=lambda s: (not s.startswith(current), s))
        
        choices = []
        if not current or "DAILY_PICKS".startswith(current):
            choices.append(app_commands.Choice(name="daily_picks (Auto-add top 5 coins)", value="daily_picks"))
            
        for match in matches[:24]:
            choices.append(app_commands.Choice(name=match, value=match))
            
        return choices[:25]

    @app_commands.command(name="monitor", description="Monitor a Binance Spot symbol")
    @app_commands.autocomplete(symbol=symbol_autocomplete)
    @app_commands.describe(timeframe="E.g., 5m, 15m, 30m, 1h, 4h, 1d (Default: 30m)")
    async def monitor(self, interaction: discord.Interaction, symbol: str, timeframe: str = DEFAULT_TIMEFRAME):
        await interaction.response.defer(thinking=True)
        
        norm_symbol = normalize_symbol(symbol)
        tf = timeframe.lower()
        
        # 1. Validation
        try:
            info = self.market_service.client.get_symbol_info(norm_symbol)
        except Exception as e:
            await interaction.followup.send(embed=build_error_embed(f"Failed to communicate with Binance API."))
            return
            
        if not info:
            await interaction.followup.send(embed=build_error_embed(f"Symbol {norm_symbol} not found on Binance."))
            return
            
        if not is_valid_spot_symbol(info):
            await interaction.followup.send(embed=build_error_embed(f"Symbol {norm_symbol} is not a valid or active Spot pair."))
            return
            
        # 2. Fetch data
        try:
            df = self.market_service.fetch_candles(norm_symbol, tf, DEFAULT_CANDLE_LIMIT)
        except Exception as e:
            await interaction.followup.send(embed=build_error_embed(f"Failed to fetch market data (invalid timeframe '{tf}'?): {str(e)}"))
            return
            
        if df.empty:
            await interaction.followup.send(embed=build_error_embed("Received empty market data."))
            return
            
        from analysis.structure import get_market_structure
        from analysis.breakout import detect_breakout
        from analysis.avp import calculate_avp
        from analysis.recommendation import build_recommendation
        from analysis.multi_tf import analyze_mtf
        from analysis.charting import generate_chart
        
        structure = get_market_structure(df)
        breakout = detect_breakout(df, structure)
        avp = calculate_avp(df, structure)
        recommendation = build_recommendation(df, structure, breakout, avp)
        mtf = analyze_mtf(norm_symbol, tf, self.market_service)
        
        last_price = float(df.iloc[-1]["close"])
        candle_count = len(df)
        
        # 3. Response
        embed = build_basic_response(norm_symbol, last_price, candle_count, tf, structure, breakout, avp, recommendation, mtf)
        
        try:
            chart_buf = generate_chart(norm_symbol, df, structure, avp)
            file = discord.File(chart_buf, filename="chart.png")
            embed.set_image(url="attachment://chart.png")
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            embed.add_field(name="Chart Error", value=str(e), inline=False)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="wl_add", description="Add a symbol or 'daily_picks' to your watchlist")
    @app_commands.autocomplete(symbol=symbol_autocomplete)
    async def wl_add(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer()
        norm = normalize_symbol(symbol)
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        
        if norm == "DAILY_PICKS":
            from services.scanner import ScannerService
            scanner = ScannerService()
            picks = scanner.get_daily_picks()
            
            if not picks:
                await interaction.followup.send("Failed to fetch daily picks.")
                return
                
            added = []
            for pick in picks:
                if ws.add(interaction.user.id, interaction.channel_id, pick):
                    added.append(pick)
                    
            if added:
                await interaction.followup.send(f"✅ Added daily picks to your watchlist:\n" + ", ".join(f"`{s}`" for s in added))
            else:
                await interaction.followup.send("⚠️ All daily picks are already in your watchlist.")
            return

        if ws.add(interaction.user.id, interaction.channel_id, norm):
            await interaction.followup.send(f"✅ Added `{norm}` to your watchlist.")
        else:
            await interaction.followup.send(f"⚠️ `{norm}` is already in your watchlist.")

    @app_commands.command(name="wl_remove", description="Remove a symbol from your watchlist")
    async def wl_remove(self, interaction: discord.Interaction, symbol: str):
        norm = normalize_symbol(symbol)
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        if ws.remove(interaction.user.id, norm):
            await interaction.response.send_message(f"🗑️ Removed `{norm}` from your watchlist.")
        else:
            await interaction.response.send_message(f"⚠️ `{norm}` was not found in your watchlist.")

    @app_commands.command(name="wl_list", description="View your watchlist")
    async def wl_list(self, interaction: discord.Interaction):
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        symbols = ws.get_user_symbols(interaction.user.id)
        if not symbols:
            await interaction.response.send_message("📭 Your watchlist is empty. Use `/wl_add` to start tracking.")
        else:
            await interaction.response.send_message(f"📋 **Your Watchlist:**\n" + ", ".join(f"`{s}`" for s in symbols))

    @app_commands.command(name="daily_picks", description="Get today's top potential coins based on volume and momentum")
    async def daily_picks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from services.scanner import ScannerService
        scanner = ScannerService()
        picks = scanner.get_daily_picks()
        
        if not picks:
            await interaction.followup.send("Failed to fetch daily picks.")
            return
            
        embed = discord.Embed(title="🌟 Today's Potential Coins", description="Coins with high liquidity and positive momentum for today.", color=discord.Color.gold())
        
        picks_str = "\n".join([f"**{i+1}.** `{symbol}`" for i, symbol in enumerate(picks)])
        embed.add_field(name="Top Picks", value=picks_str, inline=False)
        embed.set_footer(text="Updates daily. Use /wl_add to monitor them.")
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MonitorCog(bot))
