try:
    import discord
    from discord.ext import commands
    import emoji
    import requests
except ImportError:
    print(
        "Please install the dependencies before starting the bot.\nUse 'pip install -r requirements.txt' on Linux."
    )
    exit()

import os
import asyncio

from datahandler.configHandle import ConfigHandle


async def load_extension(bot):
    print("[Startup] Loading Commands...")
    for ext in os.listdir("./cogs/"):
        if ext.endswith(".py") and not ext.startswith("__"):
            await bot.load_extension("cogs." + ext[:-3])

    print("[Startup] Commands loaded.")


async def start_bot():
    print("[Startup] Prepare to start Bot...")

    ch = ConfigHandle()

    intents = discord.Intents.all()
    intents.presences = True
    intents.members = True
    bot = commands.Bot(
        command_prefix=ch.getFromConfig("command_prefix"), intents=intents
    )

    ch.config["log"] = "False"
    ch.saveConfig()
    print("[Startup] Set log to False.")

    await load_extension(bot)

    print("[Startup] Starting Bot...")
    await bot.start(ch.getFromConfig("token"))


if __name__ == "__main__":
    asyncio.run(start_bot())
