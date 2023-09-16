from sqlitedict import SqliteDict
import unittest
import time
import os
import shutil

from datahandler.tempPoll import TempPoll, XPTypes


class TestUserHandle(unittest.TestCase):
    def setUp(self):
        self.setupTime = time.time()
        self.invalidTime = 0
        self.test_data = {
            "1": [
                (self.invalidTime, XPTypes.VOICE, 1),
                (self.invalidTime, XPTypes.VOICE, 2),
                (self.setupTime, XPTypes.VOICE, 3),
                (self.setupTime, XPTypes.VOICE, 4),
                (self.setupTime, XPTypes.TEXT, 5),
                (self.setupTime, XPTypes.TEXT, 6),
            ],
            "2": [
                (self.invalidTime, XPTypes.VOICE, 10),
                (self.invalidTime, XPTypes.VOICE, 11),
                (self.setupTime, XPTypes.VOICE, 12),
                (self.setupTime, XPTypes.VOICE, 13),
                (self.setupTime, XPTypes.TEXT, 14),
                (self.setupTime, XPTypes.TEXT, 15),
            ]
        }
        os.makedirs("test/data/", exist_ok=True)
        with SqliteDict("test/data/test.sqlite") as db:
            for key, value in self.test_data.items():
                db[key] = value
            db.commit()

        self.tempPoll = TempPoll(
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
                (self.setupTime, XPTypes.VOICE, 3),
                (self.setupTime, XPTypes.VOICE, 4),
                (self.setupTime, XPTypes.TEXT, 5),
                (self.setupTime, XPTypes.TEXT, 6),
            ],
            "2": [
                (self.setupTime, XPTypes.VOICE, 12),
                (self.setupTime, XPTypes.VOICE, 13),
                (self.setupTime, XPTypes.TEXT, 14),
                (self.setupTime, XPTypes.TEXT, 15),
            ]}
        self.tempPoll.removeAllOutdatedEntries()
        self.assertEqual(tuple(expect.items()),
                         tuple(self.tempPoll.db.items()))

    def test_getAllUserSummedData(self):
        expect = {
            "1": {XPTypes.OTHER: 0, XPTypes.TEXT: 11, XPTypes.VOICE: 7},
            "2": {XPTypes.OTHER: 0, XPTypes.TEXT: 29, XPTypes.VOICE: 25},
        }
        self.assertEqual(expect, self.tempPoll.getAllUserSummedData())
