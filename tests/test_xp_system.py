import os
import shutil
import time
import unittest

import discord
from sqlitedict import SqliteDict

from databot.features.xp_system import LEVEL, TEXT, VOICE, XP, XpDataBase


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
