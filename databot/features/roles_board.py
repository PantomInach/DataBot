import logging
import discord
import json

from discord.ext import commands

from databot.config import roles_board_enabled

log = logging.getLogger(__name__)

Role = str | int

ReactionsResponse = dict[str, list[list[Role], list[Role]]]

# Key values for roles_board config files
TEXT: str = "text"
CHANNELID: str = "channelid"
MESSAGEID: str = "messageid"
REACTIONS: str = "reactions"


class RolesBoard(commands.Cog, name="Roles Board"):
    """ """

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def load_roles_boards(self, path: str):
        pass

    async def reload_roles_board(self, _):
        pass

    async def post_roles_board(self, ctx: commands.Context, roles_board_name: str):
        pass

    async def list_roles_board(self, ctx: commands.Context):
        pass

    async def list_actice_roles_board(self, ctx: commands.Context):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        pass

    @commands.Cog.listener()
    async def on_message_delete(self, payload: discord.RawMessageDeleteEvent):
        pass


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
        with open(path, "r") as f:
            board_config: dict = json.load(f)
        try:
            return SingleRolesBoard.single_roles_board_loads(board_config, bot)
        except InvalidRolesBoardConfig as irbc:
            raise InvalidRolesBoardConfig(
                f"The given roles board config from paht '{path}' is invalid:\n", irbc
            ) from irbc

    @staticmethod
    async def single_roles_board_loads(board_config: dict, bot: commands.Bot) -> "SingleRolesBoard":
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
            board_confgi: dict
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

        channel: discord.TextChannel = bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            raise InvalidRolesBoardConfig(
                f"Given channel id '{channel_id}' is not a text channel.\nType: {type(channel)}"
            )
        message: discord.Message | None = None
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            message = None
        posted: bool = message is not None

        return SingleRolesBoard(text, reactions_responses, channel_id, message_id, posted, message=message)

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
    if roles_board_enabled:
        log.info("Loaded 'Roles Board'.")
        await bot.add_cog(RolesBoard(bot))
    else:
        log.info("Did not Loaded 'Roles Board' since they are not enabled.")
