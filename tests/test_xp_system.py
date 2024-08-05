import os
import shutil
import time
import unittest

import discord
from sqlitedict import SqliteDict

from databot.features.xp_system import (LEVEL, TEXT, VOICE, XP, TempEventType,
                                        TempXpDataBase, XpDataBase)


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
            1: [(TempEventType.VOICE, 2.0, 0.0), (TempEventType.XP, 100.0, 1.0), (TempEventType.TEXT, 1, 86400.0 + 1.0), (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [(TempEventType.XP, 2.0, 86400.0 + 1.0), (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
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
            1: [(TempEventType.XP, 100.0, 1.0), (TempEventType.TEXT, 1, 86400.0 + 1.0), (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [(TempEventType.XP, 2.0, 86400.0 + 1.0), (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_4_days)
        
        self.full.max_days = 3
        data_3_days: dict = {
            1: [(TempEventType.TEXT, 1, 86400.0 + 1.0), (TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [(TempEventType.XP, 2.0, 86400.0 + 1.0), (TempEventType.XP, 100.0, 2 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
            3: [],
            4: [],
        }
        self.full.cleanup_outdated_entries(cur_time=4 * 86400.0 + 1.0)
        self.assertEqual(sqlitedict_to_dict(self.full.db), data_3_days)

        self.full.max_days = 2
        data_2_days: dict = {
            1: [(TempEventType.TEXT, 1, 2 * 86400.0 + 1.0)],
            2: [(TempEventType.XP, 100.0, 2 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 3 * 86400.0 + 1.0), (TempEventType.XP, 1.0, 4 * 86400.0 + 1.0)],
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

def sqlitedict_to_dict(sd: SqliteDict) -> dict:
    d: dict = {}
    for k, v in sd.items():
        d[int(k)] = v
    return d
