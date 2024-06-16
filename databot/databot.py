import os
import sys
import datetime
import logging
import traceback
import typing

import aiohttp
import discord

from discord.ext import commands

from .config import token

COGS_DIR: str = "databot/features"

log = logging.getLogger(__name__)


class DataBot(commands.Bot):
    client: aiohttp.ClientSession
    _uptime: datetime.datetime = datetime.datetime.utcnow()

    def __init__(self, prefix, *args, **kwargs):
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        super().__init__(*args, **kwargs, command_prefix=commands.when_mentioned_or(prefix), intents=intents)
        self.synced: bool = False

    async def load_extensions(self, path: str) -> tuple[list[str], list[str]]:
        if not os.path.isdir(path):
            log.error("Can't find dir '%s' to load cogs.", path)
            raise commands.ExtensionError(message=f"Can't find dir '{path}' to load cogs.", name=path)

        loaded_files: list[str] = []
        not_loaded_modules: list[str] = []
        for file in (f for f in os.listdir(path) if f.endswith(".py")):
            module_name: str = path.replace("/", ".") + "." + file[:-3]
            try:
                log.info("Try to load module '%s'...", module_name)
                await self.load_extension(module_name)
                loaded_files.append(module_name)
                log.info("Loaded module '%s'.", module_name)
            except commands.ExtensionError as cee:
                log.error("Failed to load extension '%s':\n%s", module_name, cee)
                not_loaded_modules.append(module_name)
        return loaded_files, not_loaded_modules

    async def on_error(self, event_method: str, *args, **kwargs):
        log.error("Error occured in method '%s'\n%s", event_method, traceback.format_exc())

    async def on_command_error(self, context, exception):
        log.error("Command error occured context=%s, exception=%s", context, exception)

    async def on_ready(self):
        log.info("Bot is ready!")

    async def setup_hook(self):
        self.client = aiohttp.ClientSession()
        await self.load_extensions(COGS_DIR)
        if not self.synced:
            commands = await self.tree.sync()
            self.synced = True
            log.info("Synced Slash commands")
            log.debug("Synced Slash commands: %s", commands)

    async def close(self):
        await super().close()
        await self.client.close()

    def run(self, *args, **kwargs):
        try:
            super().run(token, *args, **kwargs)
        except (discord.LoginFailure, KeyboardInterrupt):
            log.info("Stopping Bot...")
            sys.exit()

    @property
    def user(self) -> discord.ClientUser:
        assert super().user, "Bot is not ready"
        return typing.cast(discord.ClientUser, super().user)

    @property
    def uptime(self) -> datetime.timedelta:
        return datetime.datetime.utcnow() - self._uptime
