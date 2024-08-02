import logging
import discord
import json
import os

from discord.ext import commands

from typing import Optional

from databot.config import roles_board_enabled, roles_board_config_folder_path
from databot.command_checks import is_owner

log = logging.getLogger(__name__)

Role = str | int

ReactionsResponse = dict[str, list[list[Role], list[Role]]]

# Key values for roles_board config files
TEXT: str = "text"
CHANNELID: str = "channelid"
MESSAGEID: str = "messageid"
REACTIONS: str = "reactions"

ROLES_BOARDS_PATH: str = "roles_boards/"

class RolesBoard(commands.Cog, name="Roles Board"):
    """ """

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.single_roles_boards: list[SingleRolesBoard, ...] = None

    async def load_roles_boards(self):
        """Loads the roles boards into memory."""
        log.debug("Files in given path: %s", os.listdir(roles_board_config_folder_path))
        self.single_roles_boards = [
            await SingleRolesBoard.single_roles_board_load(
                os.path.join(roles_board_config_folder_path, file), self.bot
            )
            for file in os.listdir(roles_board_config_folder_path)
            if file.endswith(".json")
        ]

    async def update_roles_boards(self) -> list[str]:
        """Updated all posted roles boards. Changes the message text and enforces that only the reaction emojis are present."""
        posted_boards_path: list[str] = []
        for board in self.single_roles_boards:
            if board.posted:
                await self._update_single_roles_board(board)
                posted_boards_path.append(board.path)
        return posted_boards_path

    @commands.hybrid_group(name="rb", brief="Roles board commands.")
    async def roles_board(self, ctx: commands.Context):
        await ctx.send_help()

    @roles_board.command(name="reload", brief="Reloads all roles boards.")
    @is_owner()
    async def reload_roles_boards(self, ctx: commands.Context):
        await self.load_roles_boards()
        posted_boards_path: list[str] = self.update_roles_boards()
        response_message: str = "Updated active roles boards: " + ", ".join(posted_boards_path)
        log.info(response_message)
        await self.list_roles_board(ctx)

    @roles_board.command(name="post", brief="Post a roles board to the current channel.")
    @is_owner()
    async def post_roles_board(self, ctx: commands.Context, roles_board_name: str):
        board: SingleRolesBoard | None = None
        for b in self.single_roles_boards:
            if b.get_name() == roles_board_name:
                board = b
                break

        if board is None:
            await ctx.send(f"Can't find board with name '{roles_board_name}'. Configured boards: {[b.get_name() for b in self.single_roles_boards]}.", ephemeral=True)
            log.info(f"User '{ctx.author.name}' tried to post non-existant roles board '{roles_board_name}'.")
            return

        if board.posted:
            await ctx.send(f"Roles board is already posted in channel '{board.message.channel.name}'.", ephemeral=True)
            log.info(f"User '{ctx.author.name}' tried to repost roles board '{roles_board_name}'.")
            return

        message: discord.Message = await ctx.message.channel.send(board.text)
        for reaction in board.responses.keys():
            await message.add_reaction(reaction)
        board.update_posted_status(message)
        log.info(f"User '{ctx.author.name}' posted roles board '{roles_board_name}' in channel '{ctx.message.channel.name}'.")

    @post_roles_board.autocomplete("roles_board_name")
    async def post_autocomplete(self, _: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=b.get_name(), value=b.get_name())
            for b in self.single_roles_boards
            if current.lower() in b.get_name() and not b.posted
        ]

    @roles_board.command(name="list", brief="Lists all roles boards.")
    @is_owner()
    async def list_roles_board(self, ctx: commands.Context):
        posted: list[SingleRolesBoard] = []
        not_posted: list[SingleRolesBoard] = []
        for b in self.single_roles_boards:
            if b.posted:
                posted.append(b)
            else:
                not_posted.append(b)

        response: str = "```Posted Roles Boards:\n"
        for b in posted:
            response += "\t" + b.get_name() + "\n"
        response += "Not posted Roles Boards:\n"
        for b in not_posted:
            response += "\t" + b.get_name() + "\n"
        response += "```"
        await ctx.send(response, ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.bot.get_user(payload.user_id).bot:
            return

        board_and_message: discord.Message | None = await self._find_single_roles_board_and_message(
            payload.channel_id, payload.message_id
        )
        if board_and_message is None:
            log.debug("No matching roles board for message with id '%s'.", payload.message_id)
            return

        board: SingleRolesBoard = board_and_message[0]
        message: discord.Message = board_and_message[1]

        if str(payload.emoji) not in board.responses.keys():
            await message.clear_reaction(payload.emoji)
            return

        roles_add, _ = board.responses.get(str(payload.emoji))
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        member: discord.Member = guild.get_member(payload.user_id)
        await member.add_roles(*[role for role in guild.roles if role.id in roles_add])
        log.info(f"Member '{member.name}' added the reaction '{str(payload.emoji)}' to the roles board with path '{board.path}'. Added the roles '{str(roles_add)}'.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """If the reaction was removed from a roles board, then remove corresponding roles for the user."""
        if self.bot.get_user(payload.user_id).bot:
            return

        board_and_message: discord.Message | None = await self._find_single_roles_board_and_message(
            payload.channel_id, payload.message_id
        )
        if board_and_message is None:
            log.debug("No matching roles board for message with id '%s'.", payload.message_id)
            return

        board: SingleRolesBoard = board_and_message[0]

        if str(payload.emoji) not in board.responses.keys():
            return

        _, roles_remove = board.responses.get(str(payload.emoji))
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        member: discord.Member = guild.get_member(payload.user_id)
        await member.remove_roles(*[role for role in guild.roles if role.id in roles_remove])
        log.info(f"Member '{member.name}' removed his reaction '{str(payload.emoji)}' form the roles board with path '{board.path}'. Removed his roles '{str(roles_remove)}'.")

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        """When all reactions from a roles board are removed, then the options should be added back."""
        board_and_message: discord.Message | None = await self._find_single_roles_board_and_message(
            payload.channel_id, payload.message_id
        )
        if board_and_message is None:
            return

        board: SingleRolesBoard = board_and_message[0]
        message: discord.Message = board_and_message[1]
        for reaction in board.responses.keys():
            await message.add_reaction(reaction)
            log.info(f"All reactions from roles board with path '{board.path}' were removed. Readded them.")

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        """When a reaction was reaction in the responses of a roles board was cleared, add it back."""
        board_and_message: discord.Message | None = await self._find_single_roles_board_and_message(
            payload.channel_id, payload.message_id
        )
        if board_and_message is None:
            return

        board: SingleRolesBoard = board_and_message[0]
        message: discord.Message = board_and_message[1]
        if str(payload.emoji) in board.responses.keys():
            await message.add_reaction(payload.emoji)
            log.info(f"Reaction '{str(payload.emoji)}' from roles board with path '{board.path}' was removed. Readded it.")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        """Updated the SingleRolesBoard for its deletion."""
        for board in self.single_roles_boards:
            if board.message_id != payload.message_id:
                continue
            board.unposted()
            log.info(f"Roles board with path '{board.path}' was deleted from its channel. Updated the config file.")
            break

    async def _find_single_roles_board_and_message(
        self, channel_id: int, message_id: int
    ) -> Optional[tuple["SingleRolesBoard", discord.Message]]:
        """From a given channel_id and"""
        for board in self.single_roles_boards:
            if board.message_id != message_id:
                continue

            channel: discord.TextChannel = self.bot.get_channel(channel_id)
            message: discord.Message = await channel.fetch_message(message_id)

            if not board.posted:
                board.update_posted_status(message)

            return (board, message)
        return None

    async def _update_single_roles_board(self, board: "SingleRolesBoard"):
        if not board.posted:
            return
        
        if board.message.content != board.text:
            log.debug("Updated roles board '%s' text from '%s' to '%s'", board.path, board.message.content, board.text)
            await board.message.edit(content=board.text)

        for reaction in board.message.reactions:
            if str(reaction) not in board.responses:
                await board.message.clear_reaction(reaction)

        message_emojis: list[str] = [str(reaction.emoji) for reaction in board.message.reactions]
        for reaction in board.responses.keys():
            if reaction not in message_emojis:
                await board.message.add_reaction(reaction)


class NoSuchReaction(Exception):
    pass


class InvalidRolesBoardConfig(Exception):
    pass


class SingleRolesBoard:
    def __init__(
        self,
        text: str,
        responses: ReactionsResponse,
        message_id: int,
        channel_id: int,
        posted: bool,
        message: discord.Message | None = None,
        path: str | None = None,
    ):
        self.text = text
        self.responses: ReactionsResponse = responses

        assert message is not None or (
            message_id is not None and channel_id is not None
        ), "Either message or message_id and channel_id must not be None"

        self.message: discord.Message | None = message
        self.message_id: int = message_id
        self.channel_id: int = channel_id
        self.posted: bool = posted
        self.path: str | None = path

    @staticmethod
    async def single_roles_board_load(path: str, bot: commands.Bot) -> "SingleRolesBoard":
        """
        Creates a SingleRolesBoard object from a given path to a json config.

        The json config file needs the format:
            {
                "text": "Text off board",
                "channelid": channelid of message,
                "messageid": messageid of board,
                "reactions":{
                    "Emoji": [[Roles, to, give], [Roles, to, remove]],
                    "Emoji2": [[Roles, to, give], [Roles, to, remove]]
                }
            }

        Parameters:
            path: str
                Path to the json roles board config file.
            bot: commands.Bot
                Discord bot to check if the board is posted or not.

        Return:
            SingleRolesBoard
                SingleRolesBoard from the given config.

        Error:
            InvalidRolesBoardConfig
                The given json is miss configured.
        """
        with open(path, "r", encoding="UTF-8") as f:
            board_config: dict = json.load(f)
        log.debug("Deserialized roles board config from path '%s': %s", path, str(board_config))
        try:
            return await SingleRolesBoard.single_roles_board_loads(board_config, bot, path=path)
        except InvalidRolesBoardConfig as irbc:
            raise InvalidRolesBoardConfig(
                f"The given roles board config from paht '{path}' is invalid:\n", irbc
            ) from irbc

    @staticmethod
    async def single_roles_board_loads(
        board_config: dict, bot: commands.Bot, path: str | None = None
    ) -> "SingleRolesBoard":
        """
        Creates a SingleRolesBoard object from a given dictionary.

        The board_config dict needs the format:
            {
                "text": "Text off board",
                "channelid": channelid of message,
                "messageid": messageid of board,
                "reactions":{
                    "Emoji": [[Roles, to, give], [Roles, to, remove]],
                    "Emoji2": [[Roles, to, give], [Roles, to, remove]]
                }
            }

        Parameters:
            board_config: dict
                Path to the json roles board config file.
            bot: commands.Bot
                Discord bot to check if the board is posted or not.
            path: str or None
                The path from which the roles board is loaded from.
                (default: None)

        Return:
            SingleRolesBoard
                SingleRolesBoard from the given config.

        Error:
            InvalidRolesBoardConfig
                The given json is miss configured.
        """
        try:
            text: str = board_config[TEXT]
        except KeyError:
            raise InvalidRolesBoardConfig(f"Missing key'{TEXT}'.") from None
        if not isinstance(text, str):
            raise InvalidRolesBoardConfig(f"{TEXT} must be str")

        try:
            reactions_responses: ReactionsResponse = board_config[REACTIONS]
        except KeyError:
            raise InvalidRolesBoardConfig(f"Missing key '{REACTIONS}'.") from None

        is_reaction_response_type, error_message = _is_reaction_response_type(reactions_responses)
        if not is_reaction_response_type:
            raise InvalidRolesBoardConfig(f"Invalid reaction configuration.\n{error_message}")

        try:
            channel_id: int = board_config[CHANNELID]
        except KeyError:
            raise InvalidRolesBoardConfig(f"Missing key '{CHANNELID}'.") from None
        try:
            message_id: int = board_config[MESSAGEID]
        except KeyError:
            raise InvalidRolesBoardConfig(f"Missing key '{MESSAGEID}'.") from None

        if not isinstance(channel_id, int):
            raise InvalidRolesBoardConfig(f"{CHANNELID} must be int")
        if not isinstance(message_id, int):
            raise InvalidRolesBoardConfig(f"{MESSAGEID} must be int")

        message: discord.Message | None = None
        try:
            channel: discord.TextChannel | None = await bot.fetch_channel(channel_id)
            # When TextChannel exists, try to find the message with the given id.
            if not isinstance(channel, discord.TextChannel):
                raise InvalidRolesBoardConfig(
                    f"Given channel id '{channel_id}' is not a TextChannel.\nType: {type(channel)}"
                )
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            # Not created channel_ids indicate an unposted board.
            log.debug("Did not find channel with the id '%s'. Initialize roles board as unposted.", channel_id)
            message = None
            channel_id = 0
            message_id = 0
            log.debug("Could not find message with id '%s' in channel with id '%s'. Initialize roles board as unposted.", message_id, channel_id)

        posted: bool = message is not None
        srb: SingleRolesBoard = SingleRolesBoard(text, reactions_responses, message_id, channel_id, posted, message=message, path=path)
        srb.single_roles_board_dump()

        return srb

    def single_roles_board_dumps(self) -> str:
        """Dumps the single roles board to a string, which can be used to store it."""
        dict_rep: dict = {}
        dict_rep[TEXT] = self.text
        dict_rep[CHANNELID] = self.channel_id
        dict_rep[MESSAGEID] = self.message_id
        dict_rep[REACTIONS] = self.responses
        return json.dumps(dict_rep)

    def single_roles_board_dump(self, path: str | None = None):
        """
        Stores the single roles board into the file it was loaded from.

        Parameters:
            path: str or None
                The path in which the single roles board should be dumped. If not specified, the path from the object itself is used.
                (default: None)
        """
        path: str | None = path or self.path
        assert path is not None, "Can't dump SingleRolesBoard when no path is given."

        with open(path, "w", encoding="UTF-8") as f:
            f.write(self.single_roles_board_dumps())
            log.debug("Dumped roles board '%s' -> %s", self.single_roles_board_dumps(), path)

    def is_this_message(self, message: discord.Message) -> bool:
        return message == self.message or (message.id == self.message_id and message.channel.id == self.channel_id)

    def get_roles_to_add(self, emoji: str) -> list[Role]:
        if emoji not in self.responses:
            raise NoSuchReaction(f"Emoji '{emoji}' is not in the response of board.")

        return self.responses[emoji][0]

    def get_roles_to_remove(self, emoji: str) -> list[Role]:
        if emoji not in self.responses:
            raise NoSuchReaction(f"Emoji '{emoji}' is not in the response of board.")

        return self.responses[emoji][1]

    def update_posted_status(self, message: discord.Message):
        """Updated the object and its config file for information around where it is posted."""
        self.message = message
        self.posted = True
        if self.message_id != message.id and self.channel_id != message.channel.id:
            self.message_id = message.id
            self.channel_id = message.channel.id
            self.single_roles_board_dump()

    def unposted(self):
        """Updated the SingleRolesBoard state and config for the case the board is deleted."""
        self.message = None
        self.message_id = 0
        self.channel_id = 0
        self.posted = False
        self.single_roles_board_dump()

    def get_name(self) -> str:
        if self.path is None:
            return ""
        return self.path.split("/")[-1][:-5]


def _is_reaction_response_type(obj) -> (bool, str):
    """
    Checks if a given object has the type 'dict[str, list[list[Role, ...], list[Role, ...]]]',
    where 'Role' is either 'int' or 'str'.
    """
    if not isinstance(obj, dict):
        return (False, "Not a dictionary")
    for k, v in obj.items():
        if not isinstance(k, str):
            return (False, f"Key '{k}' is not a string")
        if not isinstance(v, list):
            return (False, f"Value '{v}' of key '{k}' is not a list")
        if len(v) != 2:
            return (False, f"List '{v}' of key '{k}' has not length two")
        v1, v2 = v
        if not all(isinstance(x, Role) for x in v1):
            return (False, f"Not all roles to give '{v1}' of emoji '{k}' have a role type")
        if not all(isinstance(x, Role) for x in v2):
            return (False, f"Not all roles to remove '{v2}' of emoji '{k}' have a role type")
    return (True, "")


async def setup(bot: commands.Bot):
    if not roles_board_enabled:
        raise commands.ExtensionError("Cog 'roles_board' is disabled in the config.")
    try:
        roles_board = RolesBoard(bot)
    except Exception as exc:
        log.error("Failed initialisation of RolesBoard:", exc_info=exc.__traceback__)
    await roles_board.load_roles_boards()
    await roles_board.update_roles_boards()
    await bot.add_cog(roles_board)
