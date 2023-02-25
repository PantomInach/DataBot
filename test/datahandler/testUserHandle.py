import time
import os
import shutil
import json
import unittest

from unittest.mock import MagicMock
from sqlitedict import SqliteDict

from datahandler.userHandle import UserHandle
from datahandler.configHandle import ConfigHandle


class TestUserHandle(unittest.TestCase):
    def test_isInData(self):
        for i in range(1, 11):
            self.assertTrue(
                self.userHandler.isInData(
                    i), f"User with ID {i} should be in database."
            )
            self.assertTrue(
                self.userHandler.isInData(str(i)),
                f"User with ID {i} should be in database.",
            )
        self.assertFalse(
            self.userHandler.isInData(0), "User with ID 0 should not be in database."
        )
        self.assertFalse(
            self.userHandler.isInData(
                11), "User with ID 11 should not be in database."
        )
        self.assertFalse(
            self.userHandler.isInData(100),
            "User with ID 100 should not be in database.",
        )

    def test_sortDataBy(self):
        self._populate_db_with_sorting_data()
        self.assertEqual(
            self.userHandler.sortDataBy(0),
            [
                "7",
                "8",
                "9",
                "10",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
            ],
        )
        self.assertEqual(
            self.userHandler.sortDataBy(1),
            [
                "4",
                "3",
                "2",
                "1",
                "10",
                "9",
                "8",
                "7",
                "6",
                "5",
            ],
        )
        self.assertEqual(
            self.userHandler.sortDataBy(2),
            [
                "7",
                "6",
                "5",
                "4",
                "3",
                "2",
                "1",
                "10",
                "9",
                "8",
            ],
        )

    def test_getSortedDataEntrys(self):
        self._populate_db_with_sorting_data()
        self.assertEqual(self.userHandler.getSortedDataEntrys(20, 100, 0), [])
        self.assertEqual(self.userHandler.getSortedDataEntrys(4, 1, 0), [])
        self.assertEqual(
            self.userHandler.getSortedDataEntrys(0, 100, 2),
            [
                "7",
                "6",
                "5",
                "4",
                "3",
                "2",
                "1",
                "10",
                "9",
                "8",
            ],
        )
        self.assertEqual(
            self.userHandler.getSortedDataEntrys(0, 10, 2),
            [
                "7",
                "6",
                "5",
                "4",
                "3",
                "2",
                "1",
                "10",
                "9",
                "8",
            ],
        )
        self.assertEqual(
            self.userHandler.getSortedDataEntrys(3, 10, 2),
            [
                "4",
                "3",
                "2",
                "1",
                "10",
                "9",
                "8",
            ],
        )
        self.assertEqual(
            self.userHandler.getSortedDataEntrys(3, 7, 2),
            [
                "4",
                "3",
                "2",
                "1",
            ],
        )

    def test_addNewDataEntry(self):
        t = time.time() - 60
        self.assertFalse("11" in self.userHandler.db.keys())
        self.assertFalse("12" in self.userHandler.db.keys())
        self.userHandler.addNewDataEntry("11")
        self.userHandler.addNewDataEntry(12)
        self.assertTrue("11" in self.userHandler.db.keys())
        self.assertTrue("12" in self.userHandler.db.keys())
        self.assertTrue(
            {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Level": 0,
            }.items()
            <= self.userHandler.db["11"].items(),
        )
        self.assertTrue(
            {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Level": 0,
            }.items()
            <= self.userHandler.db["12"].items(),
        )
        self.assertTrue(self.userHandler.db["11"]["Cooldown"] >= t)
        self.assertTrue(self.userHandler.db["12"]["Cooldown"] >= t)

    def test_removeUserFromData(self):
        self.assertTrue("10" in self.userHandler.db.keys())
        self.assertTrue("9" in self.userHandler.db.keys())
        self.userHandler.removeUserFromData(10)
        self.userHandler.removeUserFromData("9")
        self.assertFalse("10" in self.userHandler.db.keys())
        self.assertFalse("9" in self.userHandler.db.keys())

    def test_addTextMindCooldown(self):
        self.userHandler.db["1"] = {
            "Text": 0,
            "TextCount": 0,
            "Cooldown": 0,
        }
        self.userHandler.addTextMindCooldown(1, 10, 60)
        self.assertEqual(self.userHandler.db["1"]["Text"], 10)
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 1)
        self.assertTrue(self.userHandler.db["1"]["Cooldown"] >= self.setup_time)

        # Test that cooldown does not increase when message is send while on cooldown
        test_time = time.time()
        self.userHandler.db["1"] = {
            "Text": 0,
            "TextCount": 0,
            "Cooldown": test_time,
        }
        self.userHandler.addTextMindCooldown(1, 10, 6000000)
        self.assertEqual(self.userHandler.db["1"]["Cooldown"], test_time)
        self.assertEqual(self.userHandler.db["1"]["Text"], 0)
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 1)

    def test_addTextXP(self):
        def addTextMindCooldown(*args):
            self.userHandler._dummy = args

        self.userHandler.addTextMindCooldown = addTextMindCooldown
        self.userHandler.addTextXP("1", 10)
        self.assertEqual(self.userHandler._dummy, ("1", 10, 60))

    def test_updateLevel(self):
        self.userHandler.updateLevel("1", "1")
        self.userHandler.updateLevel(2, "1")
        self.userHandler.updateLevel("3", 1)
        self.userHandler.updateLevel(4, 1)
        self.assertEqual(self.userHandler.db["1"]["Level"], 1)
        self.assertEqual(self.userHandler.db["2"]["Level"], 1)
        self.assertEqual(self.userHandler.db["3"]["Level"], 1)
        self.assertEqual(self.userHandler.db["4"]["Level"], 1)
        self.userHandler.updateLevel("4", "2")
        self.assertEqual(self.userHandler.db["4"]["Level"], 2)
        # Test when user not in database
        self.userHandler.updateLevel(0, 1)
        self.assertFalse("0" in self.userHandler.db.keys())

    def test_getUserText(self):
        self.assertEqual(self.userHandler.getUserText(1), 0)
        self.assertEqual(self.userHandler.getUserText("1"), 0)
        entry = self.userHandler.db["2"]
        entry["Text"] = 100
        self.userHandler.db["2"] = entry
        self.assertEqual(self.userHandler.getUserText("2"), 100)

    def test_getUserVoice(self):
        self.assertEqual(self.userHandler.getUserVoice(1), 0)
        self.assertEqual(self.userHandler.getUserVoice("1"), 0)
        entry = self.userHandler.db["2"]
        entry["Voice"] = 100
        self.userHandler.db["2"] = entry
        self.assertEqual(self.userHandler.getUserVoice("2"), 100)

    def test_getUserHours(self):
        self.assertEqual(self.userHandler.getUserHours(1), 0)
        self.assertEqual(self.userHandler.getUserHours("1"), 0)
        entry = self.userHandler.db["2"]
        entry["Voice"] = 90
        self.userHandler.db["2"] = entry
        self.assertEqual(self.userHandler.getUserHours("2"), 3.0)
        entry = self.userHandler.db["3"]
        entry["Voice"] = 105
        self.userHandler.db["3"] = entry
        self.assertEqual(self.userHandler.getUserHours("3"), 3.5)
        entry = self.userHandler.db["4"]
        entry["Voice"] = 119
        self.userHandler.db["4"] = entry
        self.assertEqual(self.userHandler.getUserHours("4"), 4)
        entry = self.userHandler.db["5"]
        entry["Voice"] = 118
        self.userHandler.db["5"] = entry
        self.assertEqual(self.userHandler.getUserHours("5"), 3.9)

    def test_getUserTextCount(self):
        self.assertEqual(self.userHandler.getUserTextCount(1), 0)
        self.assertEqual(self.userHandler.getUserTextCount("1"), 0)
        entry = self.userHandler.db["2"]
        entry["TextCount"] = 100
        self.userHandler.db["2"] = entry
        self.assertEqual(self.userHandler.getUserTextCount("2"), 100)

    def test_getCooldown(self):
        self.assertEqual(self.userHandler.getCooldown(1), self.setup_time)
        self.assertEqual(self.userHandler.getCooldown("1"), self.setup_time)
        entry = self.userHandler.db["2"]
        entry["Cooldown"] = 100.0
        self.userHandler.db["2"] = entry
        self.assertEqual(self.userHandler.getCooldown("2"), 100.0)

    def test_setUserVoice(self):
        self.userHandler.setUserVoice(1, 1)
        self.userHandler.setUserVoice(2, "1")
        self.userHandler.setUserVoice("3", 1)
        self.userHandler.setUserVoice("4", "1")
        self.assertEqual(self.userHandler.db["1"]["Voice"], 1)
        self.assertEqual(self.userHandler.db["2"]["Voice"], 1)
        self.assertEqual(self.userHandler.db["3"]["Voice"], 1)
        self.assertEqual(self.userHandler.db["4"]["Voice"], 1)
        self.userHandler.setUserVoice("1", 10)
        self.assertEqual(self.userHandler.db["1"]["Voice"], 10)

    def test_setUserTextCount(self):
        self.userHandler.setUserTextCount(1, 1)
        self.userHandler.setUserTextCount(2, "1")
        self.userHandler.setUserTextCount("3", 1)
        self.userHandler.setUserTextCount("4", "1")
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 1)
        self.assertEqual(self.userHandler.db["2"]["TextCount"], 1)
        self.assertEqual(self.userHandler.db["3"]["TextCount"], 1)
        self.assertEqual(self.userHandler.db["4"]["TextCount"], 1)
        self.userHandler.setUserTextCount("1", 10)
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 10)

    def test_setUserText(self):
        self.userHandler.setUserText(1, 1)
        self.userHandler.setUserText(2, "1")
        self.userHandler.setUserText("3", 1)
        self.userHandler.setUserText("4", "1")
        self.assertEqual(self.userHandler.db["1"]["Text"], 1)
        self.assertEqual(self.userHandler.db["2"]["Text"], 1)
        self.assertEqual(self.userHandler.db["3"]["Text"], 1)
        self.assertEqual(self.userHandler.db["4"]["Text"], 1)
        self.userHandler.setUserText("1", 10)
        self.assertEqual(self.userHandler.db["1"]["Text"], 10)

    def test_setCooldown(self):
        self.userHandler.setCooldown(1, 1)
        self.userHandler.setCooldown(2, "1")
        self.userHandler.setCooldown("3", 1)
        self.userHandler.setCooldown("4", 1.0)
        self.assertEqual(self.userHandler.db["1"]["Cooldown"], 1.0)
        self.assertEqual(self.userHandler.db["2"]["Cooldown"], 1.0)
        self.assertEqual(self.userHandler.db["3"]["Cooldown"], 1.0)
        self.assertEqual(self.userHandler.db["4"]["Cooldown"], 1.0)
        self.userHandler.setCooldown("1", 10)
        self.assertEqual(self.userHandler.db["1"]["Cooldown"], 10.0)

    def test_addUserVoice(self):
        self.userHandler.addUserVoice(1, 10)
        self.userHandler.addUserVoice(2, "20")
        self.userHandler.addUserVoice("3", 30)
        self.userHandler.addUserVoice("4", "40")
        self.assertEqual(self.userHandler.db["1"]["Voice"], 10)
        self.assertEqual(self.userHandler.db["2"]["Voice"], 20)
        self.assertEqual(self.userHandler.db["3"]["Voice"], 30)
        self.assertEqual(self.userHandler.db["4"]["Voice"], 40)
        self.userHandler.addUserVoice(1, 10)
        self.assertEqual(self.userHandler.db["1"]["Voice"], 20)

    def test_addUserText(self):
        self.userHandler.addUserText(1, 10)
        self.userHandler.addUserText(2, "20")
        self.userHandler.addUserText("3", 30)
        self.userHandler.addUserText("4", "40")
        self.assertEqual(self.userHandler.db["1"]["Text"], 10)
        self.assertEqual(self.userHandler.db["2"]["Text"], 20)
        self.assertEqual(self.userHandler.db["3"]["Text"], 30)
        self.assertEqual(self.userHandler.db["4"]["Text"], 40)
        self.userHandler.addUserText(1, 10)
        self.assertEqual(self.userHandler.db["1"]["Text"], 20)

    def test_addUserTextCount(self):
        self.userHandler.addUserTextCount(1, 10)
        self.userHandler.addUserTextCount(2, "20")
        self.userHandler.addUserTextCount("3", 30)
        self.userHandler.addUserTextCount("4", "40")
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 10)
        self.assertEqual(self.userHandler.db["2"]["TextCount"], 20)
        self.assertEqual(self.userHandler.db["3"]["TextCount"], 30)
        self.assertEqual(self.userHandler.db["4"]["TextCount"], 40)
        self.userHandler.addUserTextCount(1, 10)
        self.assertEqual(self.userHandler.db["1"]["TextCount"], 20)

    def test_create_object(self):
        self.assertEqual(UserHandle(), self.userHandler)
        self.assertNotEqual(UserHandle(override_singelton=True), self.userHandler)

    def setUp(self):
        self.setup_time = time.time()
        self.test_data = {
            "1": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "2": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "3": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "4": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "5": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "6": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "7": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "8": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "9": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
            "10": {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": self.setup_time,
                "Level": 0,
            },
        }
        with SqliteDict("test.sqlite") as db:
            for key, value in self.test_data.items():
                db[key] = value
            db.commit()

        ch = ConfigHandle()
        ch.getFromConfig = MagicMock(return_value=60)
        self.userHandler = UserHandle(
            db_file_path="test.sqlite",
            override_singelton=True,
            load_from_json_if_not_init=False,
        )
        self.userHandler.ch = ch

        os.makedirs("test/data/")
        with open("test/data/userdata.json", "w") as f:
            f.write(json.dumps(self.test_data))

    def tearDown(self):
        if os.path.isfile("test.sqlite"):
            os.remove("test.sqlite")
        shutil.rmtree("test/data")

    def _populate_db_with_sorting_data(self):
        self.test_data_sorting = {
            "1": {
                "Voice": 6,
                "Text": 50,
                "TextCount": 3,
            },
            "2": {
                "Voice": 7,
                "Text": 40,
                "TextCount": 4,
            },
            "3": {
                "Voice": 8,
                "Text": 30,
                "TextCount": 5,
            },
            "4": {
                "Voice": 9,
                "Text": 20,
                "TextCount": 6,
            },
            "5": {
                "Voice": 0,
                "Text": 10,
                "TextCount": 7,
            },
            "6": {
                "Voice": 1,
                "Text": 0,
                "TextCount": 8,
            },
            "7": {
                "Voice": 2,
                "Text": 90,
                "TextCount": 9,
            },
            "8": {
                "Voice": 3,
                "Text": 80,
                "TextCount": 0,
            },
            "9": {
                "Voice": 4,
                "Text": 70,
                "TextCount": 1,
            },
            "10": {
                "Voice": 5,
                "Text": 60,
                "TextCount": 2,
            },
        }
        for key, value in self.test_data_sorting.items():
            self.userHandler.db[key] = value


if __name__ == "__main__":
    unittest.main()
