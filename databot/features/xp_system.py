import logging
import random
import time
from enum import Enum
from math import floor
from typing import Optional

import discord
from discord.ext import commands, tasks
from sqlitedict import SqliteDict

from databot.command_checks import in_channel
from databot.config import (
    command_prefix,
    guild_id,
    leaderboard_member_per_page,
    temp_xp_database_path,
    temp_xp_max_days,
    top_channel,
    xp_commit_interval,
    xp_cooldown,
    xp_database_path,
    xp_extra_factor,
    xp_long_message_len,
    xp_long_text_max,
    xp_long_text_min,
    xp_per_min,
    xp_per_vote,
    xp_roles_for_level,
    xp_system_enabled,
    xp_text_max,
    xp_text_min,
)

log = logging.getLogger(__name__)

ACTIVE_MEMBERS_FOR_XP: int = 2

# Keynames for a users data in the XP database
VOICE: str = "Voice"
TEXT: str = "Text"
XP: str = "XP"
COOLDOWN: str = "Cooldown"
LEVEL: str = "Level"

# Leaderboard visualization parameters
NICK_MAX_LEN: int = 12
NAME_AND_NICK_MAX_LEN: int = 30
NAME_AND_NICK_SEPERATOR: int = 3
RANK_SPACE: int = 4
TIME_SPACE: int = 5
TEXT_SPACE: int = 4
XP_SPACE: int = 4
LEVEL_SPACE: int = 3


XP_SYSTEM_DESCRIPTION: str = """
Group of commands in relations to gathering, managing, and visualizing stats of members.
Commands:
    top
    level
"""
XP_TOP_HELP: str = """
Spawns an interactive leaderboard in the "⏫level" via the command 'top'.
Displays the first 10 member with the highest XP total.
The sites can be changed via reacting with the ⬅️ ➡️ emojis. Use ⬅️ to go
higher and ➡️ to go lower. With ⏫ you get to the first page.

Normally the leaderboard is sorted by the total XP. You can see this if 🕰️ 💌
are reactions. When 🌟 🕰️ are available, it is sorted by messages.
When 🌟 💌 are available, it is sorted by time on guild.
You can change the sorting by reacting with 🌟 for total XP, 🕰️
for time spent on guild and 💌 for total messages send.
"""
XP_LEVEL_HELP: str = """
Gives the member a level card via the command 'level'.
This gives a short overview over the member's stats on the guild.
By adding a mention or memberID after the command the member can also view the
levelcard of other members.
"""


class TempEventType(Enum):
    VOICE = 0
    TEXT = 1
    XP = 2


class LeaderBoardSortBy(Enum):
    XP = 0
    VOICE = 1
    TEXT = 2


LeaderboardEntry = dict[str, float | int]
LeaderboardData = dict[int, LeaderboardEntry]
TempEventEntry = tuple[TempEventType, float, float]


class XpSystem(commands.Cog, name="XP System", description=XP_SYSTEM_DESCRIPTION):
    def __init__(self, bot: commands.Bot, db: "XpDataBase", temp_db: "TempXpDataBase"):
        self.bot: commands.Bot = bot
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db

    @commands.hybrid_command(name="top", description="Sends an interactive rank list.", help=XP_TOP_HELP)
    @in_channel(top_channel, allow_in_dms=False)
    async def top(
        self,
        ctx: commands.Context,
        days: Optional[float] = commands.parameter(
            description="Optional: Only show the gathered data over a given number of days"
        ),
    ):
        if days is not None:
            data: list[(int, LeaderboardEntry)] = self.temp_db.get_leaderboard_data(
                0, leaderboard_member_per_page, LeaderBoardSortBy.XP, time.time() - (days * 3600 * 24)
            )
        else:
            data: list[(int, LeaderboardEntry)] = self.db.get_leaderboard_data(
                0, leaderboard_member_per_page, LeaderBoardSortBy.XP
            )
        log.debug("Leaderboard first page data: %s", data)

        guild: discord.Guild = self.bot.get_guild(guild_id)
        user_ids: list[int] = [user_id for user_id, _ in data]
        members: dict[int, discord.Member] = {user_id: guild.get_member(user_id) for user_id in user_ids}
        leaderboard: str = render_leaderboard(data, 0, members, guild.name, days)
        await ctx.send(
            leaderboard + ctx.author.mention,
            delete_after=86400,
            view=LeaderboardButtons(self.db, self.temp_db, days=days),
        )
        try:
            await ctx.message.delete(delay=5)
        except (discord.NotFound, discord.Forbidden):
            pass

    @commands.hybrid_command(name="level", description="Returns the level of a player.", help=XP_LEVEL_HELP)
    @in_channel(top_channel, allow_in_dms=True)
    async def level(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = commands.parameter(
            description="Member of whom the level card shoul be shown"
        ),
    ):
        user_id: int = ctx.author.id
        if member is not None:
            user_id = member.id
        user: discord.Member = member or ctx.author

        avatar_url: str = user.avatar
        xp: float = self.db[user_id][XP]
        voice: float = self.db[user_id][VOICE]
        text: int = self.db[user_id][TEXT]
        level: int = self.db[user_id][LEVEL]
        next_level: int = level_calculation(xp)[1]
        try:
            nick: str = user.nick
        except AttributeError:
            nick: str = user.name

        embed = discord.Embed(title=f"{nick}     ({user.name})", color=12008408)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="TIME", value=str(voice), inline=True)
        embed.add_field(name="TEXT", value=str(text), inline=True)
        embed.add_field(
            name="EXP",
            value=f"{str(xp)}/{next_level}",
            inline=True,
        )
        embed.add_field(name="LVL", value=f"{level}", inline=True)
        content = ""
        if user_id != ctx.author.id:
            content = ctx.author.mention
        await ctx.send(embed=embed, content=content, delete_after=86400)


def render_leaderboard(
    data: list[(int, LeaderboardEntry)],
    start: int,
    members: dict[int, discord.Member],
    guild_name: str,
    temp_time: float | None = None,
) -> str:
    if temp_time is not None:
        leaderboard: str = f"**Leaderboard {guild_name} of the last {temp_time} days**\n```as"
    else:
        leaderboard: str = f"**Leaderboard {guild_name}**\n```as"
    leaderboard += render_leaderboard_users(data, start, members, display_level=temp_time is None) + "```"
    return leaderboard


def render_leaderboard_users(
    data: list[(int, LeaderboardEntry)], start: int, members: dict[int, discord.Member], display_level: bool = True
) -> str:
    leaderboard: str = ""
    if not data:
        return ""
    for rank, (user_id, entry) in enumerate(data, start=start + 1):
        member: discord.Member = members[user_id]
        if member is None:
            nick = "-X-"
            name = "ID: " + str(user_id)
        else:
            nick = member.nick or member.name
            name = member.name
        nick = "".join(c for c in nick if ord(c) < 128)
        name = "".join(c for c in name if ord(c) < 128)
        if len(nick) > NICK_MAX_LEN:
            nick = nick[: NICK_MAX_LEN - 3] + "..."
        desired_name_len: int = NAME_AND_NICK_MAX_LEN - len(nick) - NAME_AND_NICK_SEPERATOR - 2
        if len(name) > desired_name_len:
            name = name[: desired_name_len - 3] + "..."

        rank: str = str(rank).rjust(RANK_SPACE)
        name: str = ("(" + name + ")").rjust(desired_name_len + 2)
        assert len(name) + len(nick) + NAME_AND_NICK_SEPERATOR == NAME_AND_NICK_MAX_LEN
        time_str: str = leaderboard_round_time(entry[VOICE]).rjust(TIME_SPACE)
        text: str = leaderboard_round_unitless(entry[TEXT]).rjust(TEXT_SPACE)
        xp: str = leaderboard_round_float_unitless(entry[XP], XP_SPACE).rjust(XP_SPACE)
        sep: str = " " * NAME_AND_NICK_SEPERATOR
        leaderboard += f"\n{rank}. {nick}{sep}{name}   TIME: {time_str}   TEXT: {text}   EXP: {xp}"
        if display_level:
            leaderboard += "   LVL: " + str(entry[LEVEL]).rjust(LEVEL_SPACE)
    return leaderboard


def leaderboard_round_time(sec: float, spaces: int = TIME_SPACE):
    """Rounds the seconds to TIME_SPACE places using hours, days, or years if necessary."""
    ending: str = "h"
    t: float = sec / (60 * 60)
    if floor(t) >= 24 * 10 ** (spaces - 1):
        t /= 24 * 365
        ending = "a"
    elif floor(t) >= 10 ** (spaces - 1):
        t /= 24
        ending = "d"

    t = floor(10 * t) / 10
    if len(str(t)) + len(ending) > spaces:
        t = floor(t)

    if len(str(t)) > spaces:
        log.warning("Leaderboard time '%s' is to large to be contained in %s characters.", str(t) + ending, spaces)
    return str(t) + ending


def leaderboard_round_float_unitless(value: float | int, spaces: int) -> str:
    """Rounds unitless values with kilo and mega."""
    ending: str = ""
    if value >= 1_000_000:
        value /= 1_000_000
        ending = "M"
    elif value >= 10_000:
        value /= 1_000
        ending = "k"
    value = floor(10 * value) / 10
    if len(str(value)) + len(ending) > spaces:
        value = floor(value)
    rounded: str = str(value) + ending
    if len(rounded) > spaces:
        log.warning("Leaderboard value '%s' is to large to be contained in %s characters.", rounded, spaces)
    return rounded


def leaderboard_round_unitless(value: int) -> str:
    """Rounds unitless values with kilo and mega."""
    ending: str = ""
    if value >= 1_000_000:
        value /= 1_000_000
        ending = "M"
    elif value >= 10_000:
        value /= 1_000
        ending = "k"
    return str(int(value)) + ending


class LeaderboardButtons(discord.ui.View):
    def __init__(self, db: "XpDataBase", temp_db: "TempXpDataBase", days: float | None = None):
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db
        self.days: float | None = days
        self.sort_by: LeaderBoardSortBy = LeaderBoardSortBy.XP
        self.start: int = 0
        super().__init__(timeout=None)

    @discord.ui.button(label="TOP", row=0, style=discord.ButtonStyle.primary, emoji="⏫")
    async def go_to_page_one(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed TOP button.", interaction.user.name)
        if self.start != 0:
            self.start = 0
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    @discord.ui.button(label="UP", row=0, style=discord.ButtonStyle.primary, emoji="⬆")
    async def previous_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed UP button.", interaction.user.name)
        new_start: int = max(self.start - leaderboard_member_per_page, 0)
        if self.start != new_start:
            self.start = new_start
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    @discord.ui.button(label="DOWN", row=0, style=discord.ButtonStyle.primary, emoji="⬇")
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed DOWN button.", interaction.user.name)
        new_start: int = min(
            leaderboard_member_per_page * (self._leaderboard_max_user() // leaderboard_member_per_page),
            self.start + leaderboard_member_per_page,
        )
        new_start = new_start if new_start > 0 else 0
        if self.start != new_start:
            self.start = new_start
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    @discord.ui.button(label="EXP", row=1, style=discord.ButtonStyle.primary, emoji="🌟")
    async def sort_by_xp(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed EXP button.", interaction.user.name)
        if self.sort_by != LeaderBoardSortBy.XP:
            self.sort_by = LeaderBoardSortBy.XP
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    @discord.ui.button(label="TIME", row=1, style=discord.ButtonStyle.primary, emoji="⏰")
    async def sort_by_time(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed TIME button.", interaction.user.name)
        if self.sort_by != LeaderBoardSortBy.VOICE:
            self.sort_by = LeaderBoardSortBy.VOICE
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    @discord.ui.button(label="TEXT", row=1, style=discord.ButtonStyle.primary, emoji="💌")
    async def sort_by_messages(self, interaction: discord.Interaction, _: discord.ui.Button):
        log.debug("User %s pressed TEXT button.", interaction.user.name)
        if self.sort_by != LeaderBoardSortBy.TEXT:
            self.sort_by = LeaderBoardSortBy.TEXT
            leaderboard: str = await self._get_leaderboard(interaction.guild)
            await interaction.response.edit_message(content=leaderboard, view=self)
        else:
            await interaction.response.defer(ephemeral=False)

    async def _get_leaderboard(self, guild: discord.Guild) -> str:
        if self.days is not None:
            data: list[(int, LeaderboardEntry)] = self.temp_db.get_leaderboard_data(
                self.start,
                self.start + leaderboard_member_per_page,
                self.sort_by,
                time.time() - (self.days * 3600 * 24),
            )
        else:
            data: list[(int, LeaderboardEntry)] = self.db.get_leaderboard_data(
                self.start, self.start + leaderboard_member_per_page, self.sort_by
            )
        user_ids: list[int] = [user_id for user_id, _ in data]
        members: dict[int, discord.Member] = {user_id: guild.get_member(user_id) for user_id in user_ids}
        return render_leaderboard(data, self.start, members, guild.name, temp_time=self.days)

    def _leaderboard_max_user(self) -> int:
        if self.days is None:
            return len(self.db)
        return len(self.temp_db)


class XpSystemVoice(commands.Cog, name="XpSystemVoice"):
    def __init__(self, bot: commands.Bot, db: "XpDataBase", temp_db: "TempXpDataBase"):
        self.bot: commands.Bot = bot
        self.user_times: dict[discord.Member, float] = {}
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db

    @tasks.loop(seconds=xp_commit_interval)
    async def save_user_times(self):
        """
        Stores the user uptime periodicaly. Afterwards the roles are given depending on the user's level.
        """
        self.store_data()
        # Update roles
        guild: discord.Guild = self.bot.get_guild(guild_id)
        for member in guild.members:
            self._update_role(member, xp_roles_for_level)
        # Cleanup temp leaderboard
        self.temp_db.cleanup_outdated_entries()
        self.temp_db.cleanup_empty_user()

    async def _update_role(self, member: discord.Member, roles: list[(int, int)]):
        level: int = self.db[member.id][LEVEL]
        roles_to_give: list[discord.Role] = [r for l, r in roles if l >= level and r not in member.roles]
        await member.add_roles(roles_to_give)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if after is None:
            time_delta: float = self.user_times.pop(member)
            # Give user xp if he was active before.
            xp: float = self.adaptive_xp_calculation(member, time_to_xp(time_delta), voice_state=before)
            self.add_xp(member.id, xp)
        elif member not in self.user_times:
            self.user_times[member] = time.time()

    def add_xp(self, user_id: int, xp: float):
        self.db.add_xp(user_id, xp)
        self.temp_db.add_xp(user_id, xp)

    def add_voice(self, user_id: int, voice: float):
        self.db.add_voice(user_id, voice)
        self.temp_db.add_voice(user_id, voice)

    def adaptive_xp_calculation(
        self, member: discord.Member, xp: float, voice_state: Optional[discord.VoiceState] = None
    ) -> float:
        """
        Calculates the xp for a user depending on the channel the user is in.

        Increments to voice XP of member in voice channel if member is not alone in channel and is not muted.
        Gain extra XP if:
                1)  member has cam on
                2)  member is streaming

        Parameters:
            member: discord.Member
                The member, who should recive xp.
            xp: float
                The amount of xp the member should originaly get.

        Return:
            float: amount of xp the user should recive.
        """
        voice_state: discord.VoiceState = voice_state or member.voice
        if not voice_state_active(voice_state):
            return 0.0

        amount_active_user_in_channel: int = len(
            [m for m in voice_state.channel.members if voice_state_active(m.voice) and not m.bot]
        )
        if amount_active_user_in_channel < ACTIVE_MEMBERS_FOR_XP:
            return 0.0
        if voice_state.self_video or voice_state.self_stream:
            xp += xp * xp_extra_factor
        return xp

    def store_data(self):
        current_time: float = time.time()
        for user, last_time in self.user_times.items():
            time_delta: float = current_time - last_time
            self.add_voice(user.id, time_delta)
            xp: float = self.adaptive_xp_calculation(user, time_to_xp(time_delta))
            self.add_xp(user.id, xp)
        for user in self.user_times:
            self.user_times[user] = current_time

    def __del__(self):
        self.store_data()


def time_to_xp(time_delta: float) -> float:
    """
    Calculate how much xp for a given time frame should be given.

    Parameters:
        time_delta: float
            Time interval in seconds.

    Return:
        int: Resulting voice xp.
    """
    return time_delta * xp_per_min / 60


def voice_state_active(state: discord.VoiceState) -> bool:
    """
    Determines if a member is active or not depending in its voice state.

    Paramerters:
        state: discord.VoiceState

    Return:
        bool
    """
    return (
        not state.afk
        and not state.deaf
        and not state.suppress
        and not state.mute
        and not state.self_deaf
        and not state.self_mute
    )


def level_calculation(xp: float) -> (int, int):
    """
    Calculates the level of a user for a given amount of xp.

    Parameters:
        xp: float

    Return:
        int: level corresponding to the xp
    """

    level: int = 0
    level_limit: int = 100
    while xp > level_limit:
        level += 1
        level_limit += 100 + 50 * level + 5 * level**2
        # level_limit += 100 + sum(55 + y * 10 for y in range(level))  # Original calculation formular

    return level, level_limit


class XpSystemMessages(commands.Cog, name="XpSystemMessages"):
    def __init__(self, bot: commands.Bot, db: "XpDataBase", temp_db: "TempXpDataBase"):
        self.bot: commands.Bot = bot
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        member_id: int = message.author.id

        self.add_text(member_id, 1)

        cooldown: float = self.db[member_id][COOLDOWN]
        if (
            len(message.content) > 0
            and not message.content.startswith(command_prefix)
            or any(a.endswith(".jpg") or a.endswith(".png") for a in message.attachments)
        ):
            if cooldown + xp_cooldown > time.time():
                return
            self.db.update_cooldown(member_id)
            xp: float = float(
                random.randint(xp_long_text_min, xp_long_text_max)
                if len(message.content) >= xp_long_message_len
                else random.randint(xp_text_min, xp_text_max)
            )
            self.add_xp(member_id, xp)

    def add_text(self, user_id: int, tc: int):
        self.db.add_text(user_id, tc)
        self.temp_db.add_text(user_id, tc)

    def add_xp(self, user_id: int, xp: float):
        self.db.add_xp(user_id, xp)
        self.temp_db.add_xp(user_id, xp)


class XpSystemPoll(commands.Cog, name="XpSystemPoll"):
    def __init__(self, bot: commands.Bot, db: "XpDataBase", temp_db: "TempXpDataBase"):
        self.bot: commands.Bot = bot
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db

    def add_xp(self, user_id: int, xp):
        self.db.add_xp(user_id, xp)
        self.temp_db.add_xp(user_id, xp)

    @commands.Cog.listener()
    async def on_poll_vote_add(self, user: discord.Member, _: discord.PollAnswer):
        self.add_xp(user.id, float(xp_per_vote))

    @commands.Cog.listener()
    async def on_poll_vote_remove(self, user: discord.Member, _: discord.PollAnswer):
        self.add_xp(user.id, float(-xp_per_vote))


class XpDataBase:
    """Manages a sqlite database file containing the xp entries of the users.

    The database is indexed by the user's id and contains the following entries:
        {
            "Voice": float,
            "Text": int,
            "XP": float,
            "Cooldown": float,
            "Level": 0
        }

    The cooldown is the UTC time of the last send message. This is used to counteract spamming to gain xp.
    """

    def __init__(self, sqlite_db_path: str):
        self.db: SqliteDict = SqliteDict(sqlite_db_path, autocommit=True, outer_stack=True)

    def __getitem__(self, user_id: int) -> dict[str, int | float]:
        return self.db[user_id]

    def __contains__(self, user_id: int) -> bool:
        return user_id in self.db

    def __len__(self) -> int:
        return len(self.db)

    def in_data(self, user_id: int) -> bool:
        """
        Queries if the user has an entry in the database.

        Parameters:
            user_id: int

        Return:
            bool: If the user is in the database.
        """
        return user_id in self

    def add_xp(self, user_id: int, xp: float):
        """
        Adds xp to the user. Also updates the users level if necessary.

        Parameters:
            user_id: int
            xp: float
        """
        log.debug("Adding user '%s' xp: %s", str(user_id), str(xp))
        if user_id not in self:
            self.create_user(user_id)

        entry: dict = self.db[user_id]
        entry[XP] += xp
        self.db[user_id] = entry

        # Update the level of the user
        level: int = level_calculation(self.db[user_id][XP])[0]
        if self.db[user_id][LEVEL] < level:
            log.debug(
                "Increasing the level of user '%s' form '%s' to '%s'", str(user_id), str(self.db[user_id]), str(level)
            )
            entry[LEVEL] = level

        self.db[user_id] = entry

    def add_text(self, user_id: int, text: int):
        log.debug("Adding text '%s' text: %s", str(user_id), str(text))
        if user_id not in self.db:
            self.create_user(user_id)

        entry: dict = self.db[user_id]
        entry[TEXT] += text
        self.db[user_id] = entry

    def add_voice(self, user_id: int, voice: float):
        log.debug("Adding user '%s' voice: %s", str(user_id), str(voice))
        if user_id not in self.db:
            self.create_user(user_id)

        entry: dict = self.db[user_id]
        entry[VOICE] += voice
        self.db[user_id] = entry

    def create_user(self, user_id: int, voice: float = 0.0, text: int = 0, xp: float = 0.0, overwrite=False) -> bool:
        """
        Adds a new user to the database.

        Parameters:
            user_id: int
                The user id, which is used as a key for the users entry.
            voice: float
                The numberof minutes the user was on the guild.
                (default: 0.0)
            text: int
                How many messages the user has written.
                (default: 0)
            xp: float
                How much xp a user has.
                (default: 0.0)
            overwrite: bool
                If the user entry is present, overwrite the entry.
                (default: False)

        Return:
            bool: If a new entry is created.
        """
        if self.in_data(user_id) and not overwrite:
            return False

        log.info("Creating user with id '%s'.", user_id)
        self.db[user_id] = {
            VOICE: float(voice),
            TEXT: int(text),
            XP: float(xp),
            COOLDOWN: time.time() - xp_cooldown,
            LEVEL: 0,
        }
        return True

    def update_cooldown(self, user_id: int) -> bool:
        """
        Sets the users cooldown to the current time.

        Parameters:
            user_id: int

        Return:
            bool: If the user exists or not.
        """
        if not self.in_data(user_id):
            return False
        self.db[user_id][COOLDOWN] = time.time()
        return True

    def remove_user(self, user_id: int) -> Optional[dict]:
        """
        Removes the user from the database.

        Parameters:
            user_id: int

        Return:
            Optional[dict]: The user data if the user was in the database.
        """
        if not self.in_data(user_id):
            return None
        return self.db.pop(user_id)

    def get_leaderboard_data(self, start: int, end: int, sort_by: LeaderBoardSortBy) -> list[(int, LeaderboardEntry)]:
        """
        Gets the entries from the database in a given range after sorting.

        Parameters:
            start: int
                Beginning of range from which the data is extracted
            end: int
                Ending of range from which the data is extracted
            sort_by: LeaderBoardSortBy
                Sorting scheme

        Return:
            list[LeaderboardEntry]
                Range of userdata on the specified range after sorting
        """
        return slice_of_sorted_leaderboard_data(
            {int(user_id): entry for user_id, entry in self.db.items()}, sort_by, start, end
        )


class TempXpDataBase:
    """Manages a sqlite database file containing the temporary xp entries of the users.

    The database is indexed by the user's id and contains a list containing the following event entries:
        (TempEventType, float-, --float--)
    which corresponse to:
        (-type of xp--, amount, timestamp)
    """

    def __init__(self, temp_db_path: str):
        self.db = SqliteDict(temp_db_path, autocommit=True, outer_stack=True)
        self.max_days: int = temp_xp_max_days

    def __getitem__(self, user_id: int) -> list[(TempEventType, float | int, float)]:
        return self.db[user_id]

    def __contains__(self, user_id: int) -> bool:
        return user_id in self.db

    def __len__(self) -> int:
        return len(self.db)

    def create_user(self, user_id: int) -> bool:
        if user_id in self:
            return False

        log.info("Creating user with id '%s'.", user_id)
        self.db[user_id] = []
        return True

    def add_xp(self, user_id: int, xp: float):
        log.debug("Adding user '%s' xp: %s", str(user_id), str(xp))
        if user_id not in self:
            self.create_user(user_id)

        entry: list = self.db[user_id]
        entry.append((TempEventType.XP, xp, time.time()))
        self.db[user_id] = entry

    def add_text(self, user_id: int, text: int):
        log.debug("Adding text '%s' text: %s", str(user_id), str(text))
        if user_id not in self:
            self.create_user(user_id)

        entry: list = self.db[user_id]
        entry.append((TempEventType.TEXT, text, time.time()))
        self.db[user_id] = entry

    def add_voice(self, user_id: int, voice: float):
        log.debug("Adding user '%s' voice: %s", str(user_id), str(voice))
        if user_id not in self:
            self.create_user(user_id)

        entry: list = self.db[user_id]
        entry.append((TempEventType.VOICE, voice, time.time()))
        self.db[user_id] = entry

    def cleanup_empty_user(self):
        """Removes emtpy entries in the temp database."""
        for user_id in self.db.keys():
            if not self.db[user_id]:
                del self.db[user_id]

    def cleanup_outdated_entries(self, cur_time: float | None = None):
        """
        Removes all user's entries if they are to old.

        Parameters:
            cur_time: float | None
                Provide a time to compare all events to.
        """
        cur_time: float = cur_time or time.time()
        min_allowed_time: float = cur_time - self.max_days * 86400
        for user_id in self.db.keys():
            self.db[user_id] = [entry for entry in self.db[user_id] if entry[2] >= min_allowed_time]

    def sum_up_user_entry(self, user_id: int, start_timestamp: float) -> Optional[dict[str, float | int]]:
        """
        Sums up all the entries from a user where the timestamp does not predates the start_timestamp.

        Parameters:
            user_id: int
            start_timestamp: float
                Consider only entries dating after the timestamp.

        Return:
            Optional[dict[str, float | int]]
                Summation of the viable entries in this format:
                    {
                        "Voice": float,
                        "Text": int,
                        "XP": float,
                    }
                If the user does not exists, returns None
        """
        if user_id not in self.db:
            return None
        summation: dict[str, float | int] = {VOICE: 0.0, TEXT: 0, XP: 0.0}
        for event_type, amount, time_stamp in self.db[user_id]:
            if time_stamp < start_timestamp:
                continue
            match event_type:
                case TempEventType.XP:
                    summation[XP] += amount
                case TempEventType.VOICE:
                    summation[VOICE] += amount
                case TempEventType.TEXT:
                    summation[TEXT] += amount
                case _:
                    raise NotImplementedError(f"TempEventType '{event_type}' not handled.")
        return summation

    def get_leaderboard_data(
        self, start: int, end: int, sort_by: LeaderBoardSortBy, start_timestamp: float
    ) -> list[(int, LeaderboardEntry)]:
        data: LeaderboardData = dict(
            ((int(user_id), self.sum_up_user_entry(user_id, start_timestamp)) for user_id in self.db)
        )
        return slice_of_sorted_leaderboard_data(data, sort_by, start, end)


def slice_of_sorted_leaderboard_data(
    data: LeaderboardData, sort_by: LeaderBoardSortBy, start: int, end: int
) -> list[(int, LeaderboardEntry)]:
    """
    Gets the entries in a given range after sorting.

    Parameters:
        data: LeaderboardData:
            Entries from which should extracted from
        start: int
            Beginning of range from which the data is extracted
        end: int
            Ending of range from which the data is extracted
        sort_by: LeaderBoardSortBy
            Sorting scheme

    Return:
        list[LeaderboardEntry]
            Range of userdata on the specified range after sorting
    """
    return sorted(data.items(), key=lambda e: sort_leaderboard_func(e, sort_by), reverse=True)[start:end]


def sort_leaderboard_func(
    entry: tuple[int, dict[str, float | int]], sort_by: LeaderBoardSortBy
) -> (float | int, float | int):
    _, data = entry
    match sort_by:
        case LeaderBoardSortBy.XP:
            return (data[XP], data[VOICE])
        case LeaderBoardSortBy.VOICE:
            return (data[VOICE], data[XP])
        case LeaderBoardSortBy.TEXT:
            return (data[TEXT], data[XP])
        case _:
            raise RuntimeError("Invalid sort_by argument: ", sort_by)


async def setup(bot: commands.Bot):
    if not xp_system_enabled:
        raise commands.ExtensionError("Cog 'roles_board' is disabled in the config.")
    xp_per_interval: float = xp_commit_interval * xp_per_min / 60
    if xp_per_interval - int(xp_per_interval) > 0.1:
        log.warning(
            "xp_commit_interval * xp_per_min / 60 should be close to an integer to avoid missing xp. Currently %s of %s xp would be given per commit interval.",
            xp_per_interval,
            int(xp_per_interval),
        )
    try:
        db = XpDataBase(xp_database_path)
        temp_db = TempXpDataBase(temp_xp_database_path)
        xp_voice = XpSystemVoice(bot, db, temp_db)
        xp_text = XpSystemMessages(bot, db, temp_db)
        xp_poll = XpSystemPoll(bot, db, temp_db)
        xp_system = XpSystem(bot, db, temp_db)
    except Exception as exc:
        log.error("Failed initialisation of XpSystem:", exc_info=exc.__traceback__)
    await bot.add_cog(xp_voice)
    await bot.add_cog(xp_text)
    await bot.add_cog(xp_poll)
    await bot.add_cog(xp_system)
