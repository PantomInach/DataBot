import unittest
import discord

from databot.features.roles_board import (
    _is_reaction_response_type,
    ReactionsResponse,
    SingleRolesBoard,
    TEXT,
    CHANNELID,
    MESSAGEID,
    REACTIONS,
    InvalidRolesBoardConfig,
)


class TextSingelRolesBoard(unittest.IsolatedAsyncioTestCase):
    def test_is_reaction_repsonse_type(self):
        valid_reactions_response: ReactionsResponse = {"Emoji1": [[123, "456"], [789, "101112"]]}
        result, message = _is_reaction_response_type(valid_reactions_response)
        self.assertTrue(result, message)

        valid_reactions_response: ReactionsResponse = {
            "Emoji1": [[123, "456"], [789, "101112"]],
            "Emoji2": [[123, "456"], [789, "101112"]],
        }
        result, message = _is_reaction_response_type(valid_reactions_response)
        self.assertTrue(result, message)

        invalid_reactions_response: ReactionsResponse = {"Emoji1": [[123, "456"], [789, None]]}
        result, message = _is_reaction_response_type(invalid_reactions_response)
        self.assertFalse(result, message)

        invalid_reactions_response: ReactionsResponse = {"Emoji1": [[None, "456"], [789, "101112"]]}
        result, message = _is_reaction_response_type(invalid_reactions_response)
        self.assertFalse(result, message)

        invalid_reactions_response: ReactionsResponse = {10: [[123, "456"], [789, "101112"]]}
        result, message = _is_reaction_response_type(invalid_reactions_response)
        self.assertFalse(result, message)

        invalid_reactions_response: ReactionsResponse = {
            "Emoji1": [[123, "456"], [789, "101112"]],
            10: [[123, "456"], [789, "101112"]],
        }
        result, message = _is_reaction_response_type(invalid_reactions_response)
        self.assertFalse(result, message)

    async def test_single_roles_board_loads(self):
        valid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: 123,
            MESSAGEID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        await SingleRolesBoard.single_roles_board_loads(valid_config, MockBot())

        valid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: 123,
            MESSAGEID: 0,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        single_roles_board: SingleRolesBoard = await SingleRolesBoard.single_roles_board_loads(valid_config, MockBot())
        self.assertFalse(single_roles_board.posted)

        invalid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: "123",
            MESSAGEID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: 123,
            MESSAGEID: "123",
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            CHANNELID: 123,
            MESSAGEID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            CHANNELID: 123,
            MESSAGEID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            TEXT: "Sample text",
            MESSAGEID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: 123,
            REACTIONS: {"E1": [[123], [123]], "E2": [[123], [123]]},
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())

        invalid_config: dict = {
            TEXT: "Sample text",
            CHANNELID: 123,
            MESSAGEID: 123,
        }
        with self.assertRaises(InvalidRolesBoardConfig):
            await SingleRolesBoard.single_roles_board_loads(invalid_config, MockBot())


class MockResponse:
    def __init__(self):
        self.status = 404
        self.reason = ""


class MockMessage(discord.Message):
    def __init__(self, channel):
        self.channel = channel


class MockChannel(discord.TextChannel):
    def __init__(self, channel_id):
        self.id = channel_id

    async def fetch_message(self, message_id: int) -> MockMessage:
        match message_id:
            case 123:
                return MockMessage(self)
            case _:
                raise discord.NotFound(MockResponse(), "")


class MockBot:
    def get_channel(self, channel_id: int) -> MockChannel | None:
        match channel_id:
            case 123:
                return MockChannel(123)
            case _:
                return None
