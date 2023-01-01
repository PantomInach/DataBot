try:
    import discord
    from discord.ext import commands
    import emoji
    import requests
except ImportError:
    print(
        "Pleas install the dependencies before starting the bot.\nUse 'pip install -r requirements.txt' on Linux."
    )
    exit()

import os
import asyncio

from datahandler.jsonhandle import Jsonhandle


async def load_extension(bot):
    print("[Startup] Loading Commands...")
    for ext in os.listdir("./cogs/"):
        if ext.endswith(".py") and not ext.startswith("__"):
            await bot.load_extension("cogs." + ext[:-3])

    print("[Startup] Commands loaded.")


async def start_bot():
    print("[Startup] Prepare to start Bot...")

    jh = Jsonhandle()

    intents = discord.Intents.all()
    intents.presences = True
    intents.members = True
    bot = commands.Bot(
        command_prefix=jh.getFromConfig("command_prefix"), intents=intents
    )

    jh.config["log"] = "False"
    jh.saveConfig()
    print("[Startup] Set log to False.")

    await load_extension(bot)

    print("[Startup] Starting Bot...")
    await bot.start(jh.getFromConfig("token"))


if __name__ == "__main__":
    asyncio.run(start_bot())
