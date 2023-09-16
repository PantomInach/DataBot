from sqlitedict import SqliteDict
import unittest
import time
import os
import shutil

from datahandler.tempLeaderboard import TempLeaderboard, XPTypes, SortBy


class TestUserHandle(unittest.TestCase):
    def setUp(self):
        self.setupTime = time.time()
        self.validTime = self.setupTime - 86400 * 20
        self.invalidTime = 0
        self.test_data = {
            "1": [
                (self.invalidTime, XPTypes.VOICE, 1),
                (self.invalidTime, XPTypes.VOICE, 2),
                (self.validTime, XPTypes.VOICE, 3),
                (self.validTime, XPTypes.VOICE, 3),
                (self.setupTime, XPTypes.VOICE, 1),
                (self.setupTime, XPTypes.TEXT, 5),
                (self.setupTime, XPTypes.TEXT, 6),
            ],
            "2": [
                (self.invalidTime, XPTypes.VOICE, 10),
                (self.invalidTime, XPTypes.VOICE, 11),
                (self.validTime, XPTypes.VOICE, 12),
                (self.validTime, XPTypes.VOICE, 13),
                (self.setupTime, XPTypes.TEXT, 14),
                (self.setupTime, XPTypes.TEXT, 15),
            ]
        }
        os.makedirs("test/data/", exist_ok=True)
        with SqliteDict("test/data/test.sqlite") as db:
            for key, value in self.test_data.items():
                db[key] = value
            db.commit()

        self.tempLeaderboard = TempLeaderboard(
            "test/data/test.sqlite",
            True,
            30,
        )

    def tearDown(self):
        if os.path.isfile("test/data/test.sqlite"):
            os.remove("test/data/test.sqlite")
        shutil.rmtree("test/data")

    def test_removeOutdateUser(self):
        expect = {
            "1": [
                (self.validTime, XPTypes.VOICE, 3),
                (self.validTime, XPTypes.VOICE, 3),
                (self.setupTime, XPTypes.VOICE, 1),
                (self.setupTime, XPTypes.TEXT, 5),
                (self.setupTime, XPTypes.TEXT, 6),
            ],
            "2": [
                (self.validTime, XPTypes.VOICE, 12),
                (self.validTime, XPTypes.VOICE, 13),
                (self.setupTime, XPTypes.TEXT, 14),
                (self.setupTime, XPTypes.TEXT, 15),
            ]}
        self.tempLeaderboard.removeAllOutdatedEntries()
        self.assertEqual(tuple(expect.items()),
                         tuple(self.tempLeaderboard.db.items()))

    def test_getAllUserSummedData(self):
        expect = {
            "1": {XPTypes.OTHER: 0, XPTypes.TEXT: 11, XPTypes.VOICE: 7, XPTypes.TEXTCOUNT: 0},
            "2": {XPTypes.OTHER: 0, XPTypes.TEXT: 29, XPTypes.VOICE: 25, XPTypes.TEXTCOUNT: 0},
        }
        self.assertEqual(expect, self.tempLeaderboard.getAllUserSummedData())

    def test_sortDataWindowBy(self):
        expect = [
            ("2", {XPTypes.OTHER: 0, XPTypes.TEXT: 29, XPTypes.VOICE: 25, XPTypes.TEXTCOUNT: 0}),
            ("1", {XPTypes.OTHER: 0, XPTypes.TEXT: 11, XPTypes.VOICE: 7, XPTypes.TEXTCOUNT: 0}),
        ]
        self.assertEqual(expect, self.tempLeaderboard.sortDataWindowBy(SortBy.VOICE_TEXT))
        expect = [
            ("2", {XPTypes.OTHER: 0, XPTypes.TEXT: 29, XPTypes.VOICE: 0, XPTypes.TEXTCOUNT: 0}),
            ("1", {XPTypes.OTHER: 0, XPTypes.TEXT: 11, XPTypes.VOICE: 1, XPTypes.TEXTCOUNT: 0}),
        ]
        self.assertEqual(expect, self.tempLeaderboard.sortDataWindowBy(SortBy.VOICE_TEXT, window=10))
        expect = [
            ("1", {XPTypes.OTHER: 0, XPTypes.TEXT: 11, XPTypes.VOICE: 1, XPTypes.TEXTCOUNT: 0}),
            ("2", {XPTypes.OTHER: 0, XPTypes.TEXT: 29, XPTypes.VOICE: 0, XPTypes.TEXTCOUNT: 0}),
        ]
        self.assertEqual(expect, self.tempLeaderboard.sortDataWindowBy(SortBy.VOICE, window=10))

