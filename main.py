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


def start_bot():
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(load_extension(bot))
    finally:
        loop.close()
        asyncio.set_event_loop(None)

    print("[Startup] Starting Bot...")
    bot.run(jh.getFromConfig("token"))


if __name__ == "__main__":
    start_bot()
