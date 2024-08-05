import os
import shutil
import time
import unittest

import discord
from sqlitedict import SqliteDict

from databot.config import (
    command_prefix,
    xp_cooldown,
    xp_extra_factor,
    xp_long_message_len,
    xp_long_text_max,
    xp_long_text_min,
    xp_text_max,
    xp_text_min,
)
from databot.features.xp_system import (
    ACTIVE_MEMBERS_FOR_XP,
    COOLDOWN,
    LEVEL,
    TEXT,
    VOICE,
    XP,
    TempEventType,
    TempXpDataBase,
    XpDataBase,
    XpSystemMessages,
    XpSystemVoice,
    voice_state_active,
)


class TestXpDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree("temp/", ignore_errors=True)
        os.mkdir("temp/")

    @classmethod
    def tearDownClass(cls):
        os.rmdir("temp/")

    def setUp(self):
        with SqliteDict("temp/empty.sqlite", autocommit=True, outer_stack=True) as db:
            db.commit()

        self.data: dict = {
            1: {"Voice": 1.0, "Text": 1, "XP": 10.0, "Cooldown": 0.0, "Level": 0},
            2: {"Voice": 2.0, "Text": 2, "XP": 20.0, "Cooldown": 0.0, "Level": 0},
        }
        with SqliteDict("temp/full.sqlite", autocommit=True, outer_stack=True) as db:
            for k, v in self.data.items():
                db[k] = v
            db.commit()

        self.empty: XpDataBase = XpDataBase("temp/empty.sqlite")
        self.full: XpDataBase = XpDataBase("temp/full.sqlite")

    def tearDown(self):
        os.remove("temp/empty.sqlite")
        os.remove("temp/full.sqlite")

    def testDunder(self):
        # Test get items
        with self.assertRaises(KeyError):
            self.empty[0]
        with self.assertRaises(KeyError):
            self.full[0]
        self.assertEqual(self.full[1], self.data[1])

        # Test contains
        self.assertTrue(1 in self.full)
        self.assertTrue(2 in self.full)
        self.assertFalse(0 in self.full)
        self.assertFalse(0 in self.empty)

    def test_user_creation_deletion(self):
        self.assertTrue(self.empty.create_user(123))
        self.assertFalse(self.empty.create_user(123))
        self.assertTrue(123 in self.empty.db)
        self.assertIsNotNone(self.empty.remove_user(123))
        self.assertIsNone(self.empty.remove_user(123))

    def test_adding(self):
        # Adding xp level progression test
        self.empty.add_xp(123, 100.0)
        self.assertTrue(123 in self.empty.db)
        self.assertEqual(self.empty.db[123][LEVEL], 0)
        self.assertEqual(self.empty.db[123][XP], 100.0)
        self.empty.add_xp(123, 1.0)
        self.assertEqual(self.empty.db[123][XP], 101.0)
        self.assertEqual(self.empty.db[123][LEVEL], 1)
        self.empty.add_xp(123, 154.0)
        self.assertEqual(self.empty.db[123][XP], 255.0)
        self.assertEqual(self.empty.db[123][LEVEL], 1)
        self.empty.add_xp(123, 1.0)
        self.assertEqual(self.empty.db[123][XP], 256.0)
        self.assertEqual(self.empty.db[123][LEVEL], 2)
        self.empty.add_xp(123, 219.0)
        self.assertEqual(self.empty.db[123][XP], 475.0)
        self.assertEqual(self.empty.db[123][LEVEL], 2)
        self.empty.add_xp(123, 1.0)
        self.assertEqual(self.empty.db[123][XP], 476.0)
        self.assertEqual(self.empty.db[123][LEVEL], 3)
        self.empty.add_xp(123, 294.0)
        self.assertEqual(self.empty.db[123][XP], 770.0)
        self.assertEqual(self.empty.db[123][LEVEL], 3)
        self.empty.add_xp(123, 1.0)
        self.assertEqual(self.empty.db[123][XP], 771.0)
        self.assertEqual(self.empty.db[123][LEVEL], 4)

        # Level should not be decremented
        self.empty.add_xp(123, -10.0)
        self.assertEqual(self.empty.db[123][XP], 761.0)
        self.assertEqual(self.empty.db[123][LEVEL], 4)

        # Adding text counts
        self.empty.add_text(1, 1)
        self.assertTrue(1 in self.empty.db)
        self.assertEqual(self.empty[1][TEXT], 1)
        self.empty.add_text(1, 2)
        self.assertEqual(self.empty[1][TEXT], 3)
        self.empty.add_text(1, -2)
        self.assertEqual(self.empty[1][TEXT], 1)

        # Adding voice seconds
        self.empty.add_voice(2, 100.0)
        self.assertTrue(2 in self.empty.db)
        self.assertEqual(self.empty[2][VOICE], 100.0)
        self.empty.add_voice(2, 100.0)
        self.assertEqual(self.empty[2][VOICE], 200.0)
        self.empty.add_voice(2, -100.0)
        self.assertEqual(self.empty[2][VOICE], 100.0)


class TestTempXpDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree("temp/", ignore_errors=True)
        os.mkdir("temp/")

    @classmethod
    def tearDownClass(cls):
        os.rmdir("temp/")

    def setUp(self):
        with SqliteDict("temp/empty.sqlite", autocommit=True, outer_stack=True) as db:
            db.commit()

        self.data: dict = {
            1: [
                (TempEventType.VOICE, 2.0, 0.0),
                (TempEventType.XP, 100.0, 1.0),
                (TempEventType.TEXT, 1, 86400.0 + 1.0),
                (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0),
            ],
            2: [
                (TempEventType.XP, 2.0, 86400.0 + 1.0),
                (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0),
            ],
            3: [],
            4: [],
        }
        with SqliteDict("temp/full.sqlite", autocommit=True, outer_stack=True) as db:
            for k, v in self.data.items():
                db[k] = v
            db.commit()

        self.empty: TempXpDataBase = TempXpDataBase("temp/empty.sqlite")
        self.full: TempXpDataBase = TempXpDataBase("temp/full.sqlite")

    def tearDown(self):
        os.remove("temp/empty.sqlite")
        os.remove("temp/full.sqlite")

    def testDunder(self):
        # Test get items
        with self.assertRaises(KeyError):
            self.empty[0]
        with self.assertRaises(KeyError):
            self.full[0]
        self.assertEqual(self.full[1], self.data[1])

        # Test contains
        self.assertTrue(1 in self.full)
        self.assertTrue(2 in self.full)
        self.assertFalse(0 in self.full)
        self.assertFalse(0 in self.empty)

    def test_create_user(self):
        self.assertTrue(self.empty.create_user(0))
        self.assertFalse(self.empty.create_user(0))
        self.assertFalse(self.full.create_user(1))
        self.assertTrue(self.full.create_user(12))

    def test_cleanup_empty(self):
        self.assertEqual(len(self.empty.db), 0)
        self.empty.cleanup_empty_user()
        self.assertEqual(len(self.empty.db), 0)

        self.assertEqual(len(self.full.db), 4)
        self.full.cleanup_empty_user()
        self.assertEqual(len(self.full.db), 2)
        self.assertFalse(3 in self.full.db)
        self.assertFalse(4 in self.full.db)

    def test_cleanup_outdated_entries(self):
        self.full.max_days = 4
        data_4_days: dict = {
            1: [
                (TempEventType.XP, 100.0, 1.0),
                (TempEventType.TEXT, 1, 86400.0 + 1.0),
                (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0),
            ],
            2: [
                (TempEventType.XP, 2.0, 86400.0 + 1.0),
                (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0),
            ],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_4_days)

        self.full.max_days = 3
        data_3_days: dict = {
            1: [(TempEventType.TEXT, 1, 86400.0 + 1.0), (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [
                (TempEventType.XP, 2.0, 86400.0 + 1.0),
                (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0),
            ],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_3_days)

        self.full.max_days = 2
        data_2_days: dict = {
            1: [(TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [
                (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0),
                (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0),
            ],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_2_days)

        self.full.max_days = 1
        data_1_days: dict = {
            1: [],
            2: [(TempEventType.XP, 1.0, 3 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_1_days)

        self.full.max_days = 0
        data_0_days: dict = {
            1: [],
            2: [(TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_0_days)

    def test_adding(self):
        start_time: float = time.time()
        # Adding XP
        self.empty.add_xp(1, 10.0)
        self.assertTrue(1 in self.empty.db)
        self.assertEqual(self.empty.db[1][0][0], TempEventType.XP)
        self.assertEqual(self.empty.db[1][0][1], 10.0)
        self.assertTrue(time.time() > self.empty.db[1][0][2])
        self.assertTrue(self.empty.db[1][0][2] > start_time)
        self.empty.add_xp(1, 100.0)
        self.assertEqual(self.empty.db[1][1][0], TempEventType.XP)
        self.assertEqual(self.empty.db[1][1][1], 100.0)
        self.assertTrue(time.time() > self.empty.db[1][1][2])
        self.assertTrue(self.empty.db[1][1][2] > start_time)
        # Adding VOICE
        self.empty.add_voice(1, 20.0)
        self.assertEqual(self.empty.db[1][2][0], TempEventType.VOICE)
        self.assertEqual(self.empty.db[1][2][1], 20.0)
        self.assertTrue(time.time() > self.empty.db[1][2][2])
        self.assertTrue(self.empty.db[1][2][2] > start_time)
        self.empty.add_voice(2, 20.0)
        self.assertTrue(2 in self.empty.db)
        self.assertEqual(self.empty.db[2][0][0], TempEventType.VOICE)
        self.assertEqual(self.empty.db[2][0][1], 20.0)
        self.assertTrue(time.time() > self.empty.db[2][0][2])
        self.assertTrue(self.empty.db[2][0][2] > start_time)
        # Add TEXT
        self.empty.add_text(1, 1)
        self.assertEqual(self.empty.db[1][3][0], TempEventType.TEXT)
        self.assertEqual(self.empty.db[1][3][1], 1)
        self.assertTrue(time.time() > self.empty.db[1][3][2])
        self.assertTrue(self.empty.db[1][3][2] > start_time)
        self.empty.add_text(3, 1)
        self.assertTrue(3 in self.empty.db)
        self.assertEqual(self.empty.db[3][0][0], TempEventType.TEXT)
        self.assertEqual(self.empty.db[3][0][1], 1)
        self.assertTrue(time.time() > self.empty.db[3][0][2])
        self.assertTrue(self.empty.db[3][0][2] > start_time)


class TestXpSystemVoice(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.xp: XpSystemVoice = XpSystemVoice(None, None, None)
        self.addings: list[(int, TempEventType, float)] = []

        def add_xp_callback(*args, **kwargs):
            self.addings.append((args[0], TempEventType.XP, args[1]))

        def add_voice_callback(*args, **kwargs):
            self.addings.append((args[0], TempEventType.VOICE, 2.0))

        self.xp.add_xp = add_xp_callback
        self.xp.add_voice = add_voice_callback

    def test_adaptive_xp_calculation(self):
        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP - 1))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 0.0)

        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP, inactive=1))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 0.0)

        member: MockMember = MockMember()
        bot: MockMember = MockMember()
        bot.bot = True
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP, inactive=1))
        channel.members.append(bot)
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 0.0)

        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        member.voice = mvs
        member.to_inactive()
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0), 0.0)

        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 10.0)

        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        mvs.self_video = True
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 10.0 * (1 + xp_extra_factor))

        member: MockMember = MockMember()
        channel: MockChannel = MockChannel(MockMember.get_sample(ACTIVE_MEMBERS_FOR_XP))
        mvs: MockVoiceState = MockVoiceState()
        mvs.channel = channel
        mvs.self_stream = True
        self.assertEqual(self.xp.adaptive_xp_calculation(member, 10.0, mvs), 10.0 * (1 + xp_extra_factor))

    def test_store_data(self):
        def xp_calc(*args, **kwargs) -> float:
            return 1.0

        self.xp.adaptive_xp_calculation = xp_calc

        cur_time: float = time.time()
        self.xp.user_times: dict[int, float] = dict(zip(MockMember.get_id_range(2), (cur_time - 1000, cur_time - 2000)))
        self.xp.store_data()
        self.assertEqual(
            self.addings,
            [
                (1, TempEventType.VOICE, 2.0),
                (1, TempEventType.XP, 1.0),
                (2, TempEventType.VOICE, 2.0),
                (2, TempEventType.XP, 1.0),
            ],
        )
        for user_time in self.xp.user_times.values():
            self.assertGreaterEqual(user_time, cur_time)

    async def test_on_voice_state_update(self):
        def xp_calc(*args, **kwargs) -> float:
            return 1.0

        self.xp.adaptive_xp_calculation = xp_calc

        cur_time: float = time.time()
        mms: list[MockMember] = MockMember.get_id_range(2)
        self.xp.user_times: dict[int, float] = dict(zip(mms, (cur_time - 1000, cur_time - 2000)))

        await self.xp.on_voice_state_update(mms[0], None, None)
        self.assertTrue(mms[0] not in self.xp.user_times)
        self.assertEqual(self.addings, [(1, TempEventType.XP, 1.0)])

        await self.xp.on_voice_state_update(mms[0], None, True)
        self.assertTrue(mms[0] in self.xp.user_times)
        self.assertGreaterEqual(self.xp.user_times[mms[0]], cur_time)


class TestXpSystemText(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.addings: list[int, TempEventType, float] = []

        def add_xp_callback(*args, **kwargs):
            self.addings.append((args[0], TempEventType.XP, args[1]))

        def add_text_callback(*args, **kwargs):
            self.addings.append((args[0], TempEventType.TEXT, 1))

        self.xp: XpSystemMessages = XpSystemMessages(
            None, MockXpDB({1: {COOLDOWN: time.time() - xp_cooldown - 1}, 2: {COOLDOWN: time.time() - 1}}), None
        )

        self.xp.add_xp = add_xp_callback
        self.xp.add_text = add_text_callback

    async def test_on_message(self):
        message: MockMessage = MockMessage()
        await self.xp.on_message(message)
        self.assertEqual(self.addings, [(message.author.id, TempEventType.TEXT, 1)])

        self.setUp()

        bot_message: MockMessage = MockMessage()
        bot_message.author.bot = True
        await self.xp.on_message(bot_message)
        self.assertEqual(self.addings, [])

        self.setUp()

        prefix_message: MockMessage = MockMessage()
        prefix_message.content = command_prefix + "help"
        await self.xp.on_message(prefix_message)
        self.assertEqual(self.addings, [(message.author.id, TempEventType.TEXT, 1)])

        self.setUp()

        atta_message: MockMessage = MockMessage()
        atta_message.attachments = ["test.gif", "text.txt"]
        await self.xp.on_message(atta_message)
        self.assertEqual(self.addings, [(message.author.id, TempEventType.TEXT, 1)])

        self.setUp()

        atta_message: MockMessage = MockMessage()
        atta_message.attachments = ["test.gif", "text.txt", "hi.png"]
        await self.xp.on_message(atta_message)
        self.assertEqual(self.addings[0], (message.author.id, TempEventType.TEXT, 1))
        self.assertEqual(len(self.addings), 2)
        self.assertEqual(self.addings[1][0], message.author.id)
        self.assertEqual(self.addings[1][1], TempEventType.XP)

        self.setUp()

        for _ in range(100):
            message: MockMessage = MockMessage()
            message.content = "asdf"
            await self.xp.on_message(message)
            self.assertEqual(self.addings[-2], (message.author.id, TempEventType.TEXT, 1))
            self.assertEqual(self.addings[-1][0], message.author.id)
            self.assertEqual(self.addings[-1][1], TempEventType.XP)
            self.assertTrue(xp_text_max >= self.addings[-1][2] >= xp_text_min)

        for _ in range(100):
            message: MockMessage = MockMessage()
            message.content = "asdf" * xp_long_message_len
            await self.xp.on_message(message)
            self.assertEqual(self.addings[-2], (message.author.id, TempEventType.TEXT, 1))
            self.assertEqual(self.addings[-1][0], message.author.id)
            self.assertEqual(self.addings[-1][1], TempEventType.XP)
            self.assertTrue(xp_long_text_max >= self.addings[-1][2] >= xp_long_text_min)

        self.setUp()

        message: MockMessage = MockMessage()
        message.author.id = 2
        message.content = "asdf" * xp_long_message_len
        await self.xp.on_message(message)
        self.assertEqual(self.addings, [(message.author.id, TempEventType.TEXT, 1)])


class MockMember:
    def __init__(self, user_id: int = 1):
        self.bot: bool = False
        self.voice: MockVoiceState = MockVoiceState()
        self.id: int = user_id

    def to_inactive(self):
        self.voice = MockVoiceState.get_inactive()

    @staticmethod
    def get_inactive_member() -> "MockMember":
        mm: MockMember = MockMember()
        mm.voice = MockVoiceState.get_inactive()
        return mm

    @staticmethod
    def get_sample(n: int, inactive: int = 0) -> list["MockMember"]:
        assert n >= inactive, "Can't have more inactive members than members in total."
        return [MockMember() for _ in range(n - inactive)] + [MockMember.get_inactive_member() for _ in range(inactive)]

    @staticmethod
    def get_id_range(n: int) -> list["MockMember"]:
        return [MockMember(user_id=i) for i in range(1, n + 1)]


class MockChannel:
    def __init__(self, members: list[MockMember] | None = None):
        self.members: list[MockMember] = members


class MockVoiceState:
    def __init__(self):
        self.afk: bool = False
        self.deaf: bool = False
        self.suppress: bool = False
        self.mute: bool = False
        self.self_deaf: bool = False
        self.self_mute: bool = False
        self.channel: MockChannel = None

        self.self_video: bool = False
        self.self_stream: bool = False

    @staticmethod
    def get_inactive() -> "MockVoiceState":
        mvs: MockVoiceState = MockVoiceState()
        mvs.deaf = True
        assert not voice_state_active(mvs)
        return mvs


class MockMessage:
    def __init__(self, content: str = "", attachments: list[str] | None = None):
        self.author = MockMember()
        self.content: str = content
        self.attachments: list[str] = attachments or []


class MockXpDB:
    def __init__(self, data: dict):
        self.db = data

    def update_cooldown(self, *args, **kwargs):
        pass

    def __contains__(self, key):
        return key in self.db

    def __getitem__(self, key):
        return self.db[key]


def sqlitedict_to_dict(sd: SqliteDict) -> dict:
    d: dict = {}
    for k, v in sd.items():
        d[int(k)] = v
    return d
