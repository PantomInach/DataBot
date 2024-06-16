import discord
import os
import asyncio
import logging
from discord.ext.commands import Bot

from .databot import DataBot
from .config import log_file, command_prefix

log = logging.getLogger(__name__)


def run_bot():
    logging.getLogger("databot").addHandler(logging.NullHandler())
    logging.getLogger("databot").propagate = False

    logger = logging.getLogger("databot")
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)

    log_format: str = "%(asctime)s [%(levelname)s] %(filename)s@%(funcName)s: %(message)s"
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(log_format))
    logger.addHandler(ch)
    fh = logging.FileHandler(log_file, mode="a")
    fh.setFormatter(logging.Formatter(log_format))
    logger.addHandler(fh)

    bot = DataBot(prefix=command_prefix)
    bot.run()


def main():
    """Entry point for the application script"""
    run_bot()
