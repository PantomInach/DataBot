from discord.ext.commands import Bot
import discord
import os
import asyncio
from databot import config
import logging

from .features import quote

log = logging.getLogger(__name__)


async def start_bot(bot: Bot):
    log.info("[StartUp] Starting Bot...")
    await load_cogs(bot)
    await bot.start(config.token)


async def load_cogs(bot: Bot):
    log.info("Loading cogs:")
    await quote.setup(bot)


def run_bot():
    logging.getLogger("databot").addHandler(logging.NullHandler())
    logging.getLogger("databot").propagate = False

    logger = logging.getLogger("databot")
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)

    log_format: str = "%(asctime)s |[%(levelname)s]| %(filename)s@%(funcName)s: %(message)s"
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(log_format))
    logger.addHandler(ch)
    fh = logging.FileHandler(config.log_file, mode="a")
    fh.setFormatter(logging.Formatter(log_format))
    logger.addHandler(fh)

    intents = discord.Intents.all()
    intents.presences = True
    intents.members = True

    bot: Bot = Bot(config.command_prefix, intents=intents)

    asyncio.run(start_bot(bot))


def main():
    """Entry point for the application script"""
    run_bot()
