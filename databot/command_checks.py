import logging
import discord
from discord.ext import commands
from databot.config import owner_id

log = logging.getLogger(__name__)


def is_enabled(flag: bool):
    """
    Decorator for functions. If the flag is false, then the decorated function is not executed.
    Otherwise the function is run as usual.

    Parameters:
        flag: bool
            Specifies if the function should be executed.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if flag:
                return func(*args, **kwargs)
            return None

        return wrapper

    return decorator


def in_channel(channel: None | tuple[int | str], allow_in_dms: bool):
    """
    Decorator for commands. Checks if the decorated command was invoked by a user in discord in
    one of the specifed channels. If not, the command is not executed.
    If None is passed, the check is skipped.

    Parameters:
        *channel: None or int or str or a squence of int or str
            Name or id of channel, from which the command should be invoked.

        allow_in_dms: bool
            Allows the command to be run in direct messanges.
    """

    def predicate(ctx: commands.Context) -> bool:
        result: bool = False
        if isinstance(ctx.channel, discord.channel.DMChannel):
            result = allow_in_dms
        elif channel is None:
            result = True
        else:
            channels: tuple[int | str] = tuple(str(c) for c in channel)
            result = str(ctx.channel.id) in channels or ctx.channel.name in channels

        invoked_in: str = "DMChannel" if isinstance(ctx.channel, discord.channel.DMChannel) else ctx.channel.name
        if result:
            log.debug(
                "In channel check succseded for user '%s' in channel '%s'. Run command: %s",
                ctx.author.name,
                invoked_in,
                ctx.message.content,
            )
        else:
            log.debug(
                "In channel check failed for user '%s' in channel '%s'. Run command: %s",
                ctx.author.name,
                invoked_in,
                ctx.message.content,
            )
        return result

    return commands.check(predicate)


def is_in_guild(guild_id: int):
    """
    Checks if a the user invoking the command is in the given guild.

    Parameters:
        guild_id: int
            Id of the guild.
    """

    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)


def is_owner():
    """
    Checks if the user invoking the command is the owner of the bot.
    """

    def predicate(ctx):
        return ctx.author.id == owner_id

    return commands.check(predicate)
