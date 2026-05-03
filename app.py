import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN
from bot.commands import setup as setup_commands
from bot.tasks import setup as setup_tasks

class MarketScreenerBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default(),
            help_command=None
        )

    async def setup_hook(self):
        await setup_commands(self)
        await setup_tasks(self)
        await self.tree.sync()
        print("Bot commands synced!")

    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")

async def main():
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN is not set in environment or .env file.")
        return
        
    bot = MarketScreenerBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
