import discord
from discord.ext import commands

import os

from datahandler.jsonhandel import Jsonhandel

print("[Startup] Prepare to start Bot...")

jh = Jsonhandel()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=jh.getFromConfig("command_prefix"), intents=intents)

jh.config["log"] = "False"
jh.saveConfig()
print("[Startup] Set log to False.")
print("[Startup] Loading Commands...")
for ext in os.listdir("./cogs/"):
    if ext.endswith(".py"):
        bot.load_extension("cogs." + ext[:-3])

print("[Startup] Commands loaded.")

print("[Startup] Starting Bot...")
bot.run(jh.getFromConfig("token"))
