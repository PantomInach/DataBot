import discord
import logging
import re

from discord.ext import commands
from databot.config import dynamic_channel_enabled, guild_id
from databot.command_checks import is_owner

log = logging.getLogger(__name__)

IDENTIFIER: str = "#"
REGEX: re.Pattern = re.compile(f".*{IDENTIFIER}\\d+$")

DCGroups = dict[str, dict[int, discord.VoiceChannel]]


class DynamicChannelCog(commands.Cog, name="Dynamic Channel"):
    """
    Dynamicly creates channel ending with the IDENTIFIER and a number if needed.
    """

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    @commands.has_permissions(manage_channels=True)
    async def on_voice_state_update(self, _, before: discord.VoiceState, after: discord.VoiceState):
        if (
            before.channel is not None
            and isinstance(before.channel, discord.VoiceChannel)
            and _is_dynamic_channel(before.channel)
        ):
            log.debug("Enter handle user disconnect.")
            await self._handel_user_disconnect(before.channel)
        if (
            after.channel is not None
            and isinstance(after.channel, discord.VoiceChannel)
            and _is_dynamic_channel(after.channel)
        ):
            log.debug("Enter handle user connected.")
            await self._handel_user_connect(after.channel)

    async def _handel_user_connect(self, channel: discord.VoiceChannel):
        if len(channel.members) > 1:
            return

        await _create_next_free_dynamic_channel_if_needed(channel)

    async def _handel_user_disconnect(self, channel: discord.VoiceChannel):
        if len(channel.members) > 0:
            return

        await _delete_empty_dynamic_channel_except_first(channel)

    @commands.command(name="cleanup_dc")
    @is_owner()
    @commands.has_permissions(manage_channels=True)
    async def clean_up_dynamic_channel_command(self, _):
        await _clean_up_dynamic_channel(self.bot.get_guild(guild_id))


async def _clean_up_dynamic_channel(guild: discord.Guild):
    """
    Removes all empty dynamic voice channel except the lowest one.
    Then renames all dynamic voice channel such that the numbering is consecutive.
    Ensures that the dynamic voice channel are ordered correctly.

    Parameters:
        guild: discord.Guild
            Guild on which the operation should be performed.
    """
    groups: DCGroups = _group_dynamic_channel(guild.channels)
    for base_name in groups:
        await _delete_empy_dynamic_channel_except_first_from_base_name(base_name, groups)

    groups: DCGroups = _group_dynamic_channel(guild.channels)
    for dc_groups in groups.values():
        sorted_by_num: list[tuple[int, discord.VoiceChannel]] = sorted(dc_groups.items(), key=lambda x: x[0])
        i = 1
        for num, vc in sorted_by_num:
            if num != i:
                await vc.edit(name=base_name + IDENTIFIER + str(i))
            i += 1
        for i in range(1, len(sorted_by_num)):
            (_, vc1), (_, vc2) = sorted_by_num[i - 1 : i + 1]
            if vc1.position + 1 != vc2.position:
                await vc2.move(after=vc1)


def _is_dynamic_channel(channel: discord.VoiceChannel) -> bool:
    """
    Test if the given voice channels' name qualifies as a dynamic voice channel name.
    A dynamic voice channel name must end with the IDENTIFIER followed by a number.

    Parameter:
        discord.VoiceChannel

    Return:
        bool
            Is the channel a dynamic voice channel.
    """
    return bool(isinstance(channel, discord.VoiceChannel) and REGEX.match(channel.name))


def _filter_for_dynamic_channel(channels: list[discord.VoiceChannel]) -> list[discord.VoiceChannel]:
    """
    From a given list of voice channel, filter out all non dynamic channel and return the list.
    A dynamic channel is identified by ending the IDENTIFIER and a number.

    Parameters:
        channels: list[discord.VoiceChannel]
            List of VoiceChannel.

    Return:
        list[discord.VoiceChannel]
            List of dynamic VoiceChannel
    """
    return list(filter(_is_dynamic_channel, channels))


def _group_dynamic_channel(channels: list[discord.VoiceChannel]) -> DCGroups:
    """
    Groups the dynamic voice channel by their base name.
    Within each groupe the channels are stored in a dict with their number as an id.

    Parameters:
        channels: list[discord.VoiceChannel]

    Return:
        Dict of grouped dynamic voice channels.
    """
    groups: DCGroups = {}
    for channel in channels:
        option = _dynamic_channel_base_name_and_number(channel)
        if option is not None:
            base_name, number = option
            groups.setdefault(base_name, {})[number] = channel
    return groups


def _dynamic_channel_base_name(channel: discord.VoiceChannel) -> str:
    """
    Gets the name of a dynamic channel without the identifier and its number.
    If the channel is not a dynamic channel, then the channel name will be returned.

    Parameter:
        discord.VoiceChannel

    Return:
        Base name of the dynamic channel.
    """
    if _is_dynamic_channel(channel):
        return IDENTIFIER.join(channel.name.split(IDENTIFIER)[:-1])
    return channel.name


def _dynamic_channel_number(channel: discord.VoiceChannel) -> int | None:
    """
    Gets the number of a of a dynamic voice channel.

    Paramter:
        discord.VoiceChannel

    Return:
        Number of the channel.
        If the channel is not dynamic, then None is returned.
    """
    if _is_dynamic_channel(channel):
        return int(channel.name.split(IDENTIFIER)[-1])
    return None


def _dynamic_channel_base_name_and_number(channel: discord.VoiceChannel) -> tuple[str, int] | None:
    """
    Gives the base name and the number of a dynamic channel.

    Parameter:
        discord.VoiceChannel

    Return:
        Base name and number if the channel is dynamic.
        Else, None.
    """
    if _is_dynamic_channel(channel):
        parts: list[str] = channel.name.split(IDENTIFIER)
        return (IDENTIFIER.join(parts[:-1]), int(parts[-1]))
    return None


def _next_free_number_from_groups(groups: DCGroups, channel: discord.VoiceChannel) -> int:
    """
    Finds the next free number of the dynamic voice channel of the channel's base name.

    Parameters:
        groups: dict[str, dict[int, discord.VoiceChannel]]
            Grouping of dynamic voice channel by their base name and number.
        channel: discord.VoiceChannel
            Dynamic voice channel whos base name is used.

    Return:
        int
            First available number a new dynamic voice channel can have.
    """
    i = 1
    numbers: set[int] = set(groups[_dynamic_channel_base_name(channel)].keys())
    while i in numbers:
        i += 1
    return i


def _exist_free_dynamic_channel(groups: DCGroups, base_name: str) -> bool:
    """
    Checks if there exists a empty dynamic voice channel with the given base name.

    Parameters:
        groups: dict[str, dict[int, discord.VoiceChannel]]
            Grouping of dynamic voice channel by their base name and number.
        base_name: str

    Return:
        bool
    """
    return any(len(vc.members) == 0 for vc in groups[base_name].values())


def _free_dynamic_channel(groups: DCGroups, base_name: str) -> dict[int, discord.VoiceChannel]:
    """
    Gets all the empty dynamic voice channel with the given base name.

    Parameters:
        groups: dict[str, dict[int, discord.VoiceChannel]]
            Grouping of dynamic voice channel by their base name and number.
        base_name: str

    Return:
        dict[int, discord.VoiceChannel]
            All empty dynamic voice channel with the given base name.
    """
    return dict((n, vc) for n, vc in groups[base_name].items() if len(vc.members) == 0)


async def _delete_empty_dynamic_channel_except_first(channel: discord.VoiceChannel):
    """
    Deletes all empty dynamic voice channel with the matching base_name of the given channel,
    except the first one depending on the dynamic channel's number.

    Parametes:
        channel: discord.VoiceChannel
            Defines the group of dynamic channel worked with.
            Needs to be a dynamic voice channel.
    """
    guild: discord.Guild = channel.guild
    base_name = _dynamic_channel_base_name(channel)
    groups: DCGroups = _group_dynamic_channel(guild.channels)

    await _delete_empy_dynamic_channel_except_first_from_base_name(base_name, groups)


async def _delete_empy_dynamic_channel_except_first_from_base_name(base_name: str, groups: DCGroups):
    """
    Deletes all empty dynamic voice channel with the matching base_name, except the first one
    depending on the dynamic channel's number.

    Parametes:
        base_name: str
        groups: dict[str, dict[int, discord.VoiceChannel]]
            Grouping of dynamic voice channel by their base name and number.
    """
    empty_channel: dict[int, discord.VoiceChannel] = _free_dynamic_channel(groups, base_name)
    empty_channel_sorted_by_num: list[int, discord.VoiceChannel] = sorted(empty_channel.items(), key=lambda x: x[0])
    for _, vc in empty_channel_sorted_by_num[1:]:
        log.debug("Deleting empty dynamic voice channel '%s'", vc.name)
        await vc.delete()


async def _create_next_free_dynamic_channel_if_needed(channel: discord.VoiceChannel):
    """
    Creates a new dynamic voice channel based on the given dynamic voice channel if no other empty
    dynamic channel with the same base name exists.

    Parametes:
        channel: discord.VoiceChannel
            Dynamic voice channel which will be copied and whos base name will be used.
            Needs to be a dynamic channel.
    """
    base_name: str = _dynamic_channel_base_name(channel)
    guild: discord.Guild = channel.guild
    groups: DCGroups = _group_dynamic_channel(guild.channels)

    if _exist_free_dynamic_channel(groups, base_name):
        return

    next_number: int = _next_free_number_from_groups(groups, channel)

    # new_channel: discord.VoiceChannel = await channel.clone(name=base_name + IDENTIFIER + str(next_number))
    # await new_channel.move(after=groups[base_name][next_number - 1])
    new_channel: discord.VoiceChannel = await guild.create_voice_channel(
        name=base_name + IDENTIFIER + str(next_number),
        overwrites=channel.overwrites,
        category=channel.category,
        position=groups[base_name][next_number - 1].position + 1,
        bitrate=channel.bitrate,
        user_limit=channel.user_limit,
        rtc_region=channel.rtc_region,
        video_quality_mode=channel.video_quality_mode,
    )
    log.debug(
        "Cloned new channel with name '%s' from '%s'.",
        new_channel.name,
        channel.name,
    )


async def setup(bot: commands.Bot):
    if dynamic_channel_enabled:
        log.info("Loaded 'Dynamic Channel'.")
        await bot.add_cog(DynamicChannelCog(bot))
    else:
        log.info("Did not Loaded 'Dynamic Channel' since they are not enabled.")
