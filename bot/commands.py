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
        from analysis.marketcap import fetch_marketcap_data
        
        structure = get_market_structure(df)
        breakout = detect_breakout(df, structure)
        avp = calculate_avp(df, structure)
        recommendation = build_recommendation(df, structure, breakout, avp)
        mtf = analyze_mtf(norm_symbol, tf, self.market_service)
        marketcap = fetch_marketcap_data(norm_symbol)
        
        last_price = float(df.iloc[-1]["close"])
        candle_count = len(df)
        
        # 3. Response
        embed = build_basic_response(norm_symbol, last_price, candle_count, tf, structure, breakout, avp, recommendation, mtf, marketcap)
        
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

        # Validate symbol exists on Binance before adding
        try:
            info = self.market_service.client.get_symbol_info(norm)
            if not info:
                await interaction.followup.send(embed=build_error_embed(f"Symbol `{norm}` not found on Binance."))
                return
        except Exception:
            await interaction.followup.send(embed=build_error_embed("Failed to validate symbol with Binance API."))
            return

        if ws.add(interaction.user.id, interaction.channel_id, norm):
            await interaction.followup.send(f"✅ Added `{norm}` to your watchlist.")
        else:
            await interaction.followup.send(f"⚠️ `{norm}` is already in your watchlist.")

    @app_commands.command(name="wl_remove", description="Remove a symbol from your watchlist")
    async def wl_remove(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer()
        norm = normalize_symbol(symbol)
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        if ws.remove(interaction.user.id, norm):
            await interaction.followup.send(f"🗑️ Removed `{norm}` from your watchlist.")
        else:
            await interaction.followup.send(f"⚠️ `{norm}` was not found in your watchlist.")

    @app_commands.command(name="wl_list", description="View your watchlist")
    async def wl_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        symbols = ws.get_user_symbols(interaction.user.id)
        if not symbols:
            await interaction.followup.send("📭 Your watchlist is empty. Use `/wl_add` to start tracking.")
        else:
            await interaction.followup.send(f"📋 **Your Watchlist:**\n" + ", ".join(f"`{s}`" for s in symbols))

    @app_commands.command(name="wl_clear", description="Clear your entire watchlist")
    async def wl_clear(self, interaction: discord.Interaction):
        await interaction.response.defer()
        from services.watchlist import WatchlistService
        ws = WatchlistService()
        symbols = ws.get_user_symbols(interaction.user.id)
        if not symbols:
            await interaction.followup.send("📭 Your watchlist is already empty.")
            return
        count = 0
        for sym in list(symbols):
            if ws.remove(interaction.user.id, sym):
                count += 1
        await interaction.followup.send(f"🗑️ Cleared **{count}** symbols from your watchlist.")

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

    @app_commands.command(name="mcap", description="Cek market cap dan deteksi sinyal akumulasi/distribusi suatu coin")
    @app_commands.autocomplete(symbol=symbol_autocomplete)
    @app_commands.describe(symbol="Simbol coin, contoh: BTCUSDT, ETHUSDT, SOLUSDT")
    async def mcap(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(thinking=True)

        norm_symbol = normalize_symbol(symbol)

        from analysis.marketcap import fetch_marketcap_data, format_market_cap
        mcap = fetch_marketcap_data(norm_symbol)

        if not mcap.available:
            await interaction.followup.send(embed=build_error_embed(
                f"Tidak dapat mengambil data market cap untuk `{norm_symbol}`.\n"
                f"Pastikan simbol valid dan tersedia di CoinGecko.\n\n"
                f"*{mcap.interpretation}*"
            ))
            return

        divergence = mcap.market_cap_change_24h - mcap.price_change_24h
        mcap_str = format_market_cap(mcap.market_cap)

        # Tentukan warna embed berdasarkan sinyal
        color_map = {
            "accumulation": discord.Color.from_rgb(0, 200, 100),
            "distribution": discord.Color.from_rgb(220, 50, 50),
            "aligned_up": discord.Color.green(),
            "aligned_down": discord.Color.red(),
            "neutral": discord.Color.greyple(),
        }
        color = color_map.get(mcap.signal, discord.Color.blue())

        embed = discord.Embed(
            title=f"{mcap.signal_emoji} Market Cap: {norm_symbol}",
            description=f"**{mcap.signal_label}**\n\n{mcap.interpretation}",
            color=color
        )

        embed.add_field(
            name="📊 Data 24h",
            value=(
                f"**Market Cap:** {mcap_str}\n"
                f"**Perubahan Harga:** {mcap.price_change_24h:+.2f}%\n"
                f"**Perubahan MCap:** {mcap.market_cap_change_24h:+.2f}%\n"
                f"**Divergensi MCap-Harga:** {divergence:+.2f}%"
            ),
            inline=True
        )

        # Panduan interpretasi divergensi
        if mcap.signal == "accumulation":
            guide = (
                "✅ **MCap > Harga** berarti supply bertambah tapi harga gak naik setimpal.\n"
                "Ini tanda bahwa ada *smart money* yang akumulasi diam-diam.\n"
                "**Strategi:** Pantau breakout dari resistance terdekat sebagai konfirmasi entry."
            )
        elif mcap.signal == "distribution":
            guide = (
                "⚠️ **Harga > MCap** berarti pump tidak didukung modal besar.\n"
                "Kemungkinan ada *retail FOMO* yang mendorong harga naik tanpa akumulasi nyata.\n"
                "**Strategi:** Hati-hati masuk, waspadai reversal cepat."
            )
        elif mcap.signal == "aligned_up":
            guide = (
                "📈 Kenaikan organik — harga dan market cap naik bersamaan.\n"
                "Sinyal bullish yang sehat dan berkelanjutan.\n"
                "**Strategi:** Bisa ikut trend, tapi tetap perhatikan level resistance."
            )
        elif mcap.signal == "aligned_down":
            guide = (
                "📉 Penjualan terkoordinasi — harga dan market cap turun bersamaan.\n"
                "Sinyal bearish, hindari masuk dulu.\n"
                "**Strategi:** Tunggu stabilisasi atau cari level support kuat."
            )
        else:
            guide = "Pergerakan terlalu kecil untuk memberikan sinyal yang berarti. Tunggu konfirmasi lebih lanjut."

        embed.add_field(name="💡 Interpretasi & Strategi", value=guide, inline=False)
        embed.add_field(
            name="ℹ️ Cara Baca Divergensi",
            value=(
                "`MCap Change - Price Change = Divergensi`\n"
                "• **Divergensi > +2.5%** → Akumulasi tersembunyi\n"
                "• **Divergensi < -2.5%** → Pump lemah / distribusi\n"
                "• **Mendekati 0%** → Pergerakan normal / seimbang"
            ),
            inline=False
        )
        embed.set_footer(text=f"Data via CoinGecko (ID: {mcap.coin_id}) • Cache 5 menit")
        import datetime
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MonitorCog(bot))
