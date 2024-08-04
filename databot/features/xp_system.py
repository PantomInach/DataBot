import logging
import random
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import discord
from discord.ext import commands, tasks
from sqlitedict import SqliteDict

from databot.config import (command_prefix, guild_id, temp_xp_database_path,
                            temp_xp_max_days, xp_commit_interval, xp_cooldown,
                            xp_database_path, xp_extra_factor,
                            xp_long_message_len, xp_long_text_max,
                            xp_long_text_min, xp_per_min, xp_roles_for_level,
                            xp_system_enabled, xp_text_max, xp_text_min)

log = logging.getLogger(__name__)

ACTIVE_MEMBERS_FOR_XP: int = 2

# Keynames for a users data in the XP database
VOICE: str = "Voice"
TEXT: str = "Text"
XP: str = "XP"
COOLDOWN: str = "Cooldown"
LEVEL: str = "Level"


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
            if user.id not in self.db:
                self.db.create_user(user.id)

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


def level_calculation(xp: float) -> int:
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
        level_limit += 100 + sum(55 + y * 10 for y in range(level))
        # TODO: Make it more efficient
        # level_limit: int = 100 + 55 * (level - 1) + 5 * level * (level - 1)
    return level


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
        if member_id not in self.db:
            self.db.create_user(member_id)
            self.temp_db.create_user(member_id)

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
        self.db.add_text(user_id, tc, self.db, self.temp_db)
        self.temp_db.add_text(user_id, tc, self.db, self.temp_db)

    def add_xp(self, user_id: int, xp: float):
        self.db.add_xp(user_id, xp)
        self.temp_db.add_xp(user_id, xp)


class XpSystemPoll(commands.Cog, name="XpSystemPoll"):
    # TODO: Track poll participation
    def __init__(self, bot: commands.Bot, db: "XpDataBase", temp_db: "TempXpDataBase"):
        self.bot: commands.Bot = bot
        self.db: XpDataBase = db
        self.temp_db: TempXpDataBase = temp_db

    def add_xp(self, user_id: int, xp):
        # TODO
        raise NotImplementedError


class XPDB(ABC):
    # TODO: Needed?
    @abstractmethod
    def add_voice(self, user_id: int, voice: float):
        pass

    @abstractmethod
    def add_text(self, user_id: int, text: int):
        pass

    @abstractmethod
    def add_xp(self, user_id: int, xp: float):
        pass


class XpDataBase(XPDB):
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
        level: int = level_calculation(self.db[user_id][XP])
        if self.db[user_id][LEVEL] < level:
            log.debug(
                "Increasing the level of user '%s' form '%s' to '%s'", str(user_id), str(self.db[user_id]), str(level)
            )
            entry[LEVEL] = level

        self.db[user_id] = entry

    def add_text(self, user_id: int, text: int):
        log.debug("Adding text '%s' voice: %s", str(user_id), str(text))
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


class TempEventType(Enum):
    VOICE = 0
    TEXT = 1
    XP = 2


class TempXpDataBase(XPDB):
    """Manages a sqlite database file containing the temporary xp entries of the users.

    The database is indexed by the user's id and contains a list containing the following event entries:
        (TempEventType, float-, --float--)
    which corresponse to:
        (-type of xp--, amount, timestamp)
    """

    def __init__(self, temp_db_path: str):
        self.db = SqliteDict(temp_db_path, autocommit=True, outer_stack=True)

    def __getitem__(self, user_id: int) -> list[(TempEventType, float | int, float)]:
        return self.db[user_id]

    def __contains__(self, user_id: int) -> bool:
        return user_id in self.db

    def create_user(self, user_id: int) -> bool:
        if user_id in self:
            return False

        log.info("Creating user with id '%s'.", user_id)
        self.db[user_id] = []
        return True

    def add_xp(self, user_id: int, xp: float):
        log.debug("Adding user '%s' xp: %s", str(user_id), str(xp))
        if user_id not in self:
            self.db.create_user(user_id)

        self.db[user_id].append((TempEventType.XP, xp, time.time()))

    def add_text(self, user_id: int, text: int):
        log.debug("Adding text '%s' voice: %s", str(user_id), str(text))
        if user_id not in self:
            self.db.create_user(user_id)

        self.db[user_id].append((TempEventType.TEXT, text, time.time()))

    def add_voice(self, user_id: int, voice: float):
        log.debug("Adding user '%s' voice: %s", str(user_id), str(voice))
        if user_id not in self:
            self.db.create_user(user_id)

        self.db[user_id].append((TempEventType.VOICE, voice, time.time()))

    def cleanup_empty_user(self):
        """Removes emtpy entries in the temp database."""
        for user_id in self.db.keys():
            if not self.db[user_id]:
                del self.db[user_id]

    def cleanup_outdated_entries(self):
        """Removes all user's entries if they are to old."""
        min_allowed_time: float = time.time() - temp_xp_max_days * 86400
        for user_id in self.db.keys():
            self.db[user_id] = [entry for entry in self.db[user_id] if entry[2] >= min_allowed_time]


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
    except Exception as exc:
        log.error("Failed initialisation of XpSystem:", exc_info=exc.__traceback__)
    await bot.add_cog(xp_voice)
    await bot.add_cog(xp_text)
