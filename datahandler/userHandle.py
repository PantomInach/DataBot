import json
import os
import time
import atexit

from sqlitedict import SqliteDict

from typing import Iterable
from datahandler.configHandle import ConfigHandle
from datahandler.tempLeaderboard import TempLeaderboard, XPTypes


class UserHandle(object):
    """
    Handles manipulation and reading from userdata.json
    """

    _instance = None

    def __new__(
        cls,
        db_file_path=None,
        override_singelton=False,
        load_from_json_if_not_init=True,
        data_path=None,
    ):
        """Singelton pattern."""
        if cls._instance is None or override_singelton:
            cls._instance = super(UserHandle, cls).__new__(cls)
            if data_path:
                cls.datapath = data_path
            else:
                cls.datapath = (
                    str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
                )
            if not db_file_path:
                cls.db_path = cls.datapath + "userdata.sqlite"
            else:
                cls.db_path = db_file_path

            cls.db = SqliteDict(cls.db_path, outer_stack=True, autocommit=True)
            if (
                load_from_json_if_not_init
                and not cls.db
                and os.path.isfile(cls.datapath + "userdata.json")
            ):
                # When database is empty try to import the older json file storing the
                # userdata. This ensures backwards compatablity with version <= 2.2.1.
                with open(cls.datapath + "userdata.json", "r") as j:
                    for key, value in json.load(j).items():
                        cls.db[key] = value

            cls.ch = ConfigHandle()
            cls.tempLeaderboard = TempLeaderboard()
            atexit.register(UserHandle._cleanup, cls.db)
        return cls._instance

    """
        Functions to manipulate the userdata.json
    """

    def isInData(self, userID: str | int) -> bool:
        """
        Tests if the user has an entry in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        return str(userID) in self.db.keys()

    def sortDataBy(self, sortBy: int):
        """
        Sorts userdata.json depending on sortBy.

        Keyword arguments:
        sortBy -- 0 => Sort by voice + text
            1 => Sort by voice
            2 => Sort by textcount
        """
        sortMask = [[1, 1, 0], [0, 1, 0], [0, 0, 1]]  # Sorting mask
        sortedData = sorted(
            self.db,
            key=lambda id: sortMask[sortBy][0] * self.getUserText(id)
            + sortMask[sortBy][1] * self.getUserVoice(id)
            + sortMask[sortBy][2] * self.getUserTextCount(id),
            reverse=True,
        )
        return sortedData

    def getSortedDataEntrys(self, entryBegin: int, entryEnd: int, sortBy: int):
        """
        Sorts Data by given parameter and returns the given entries.

        Keyword arguments:
        entrBeginn -- Begin of user entry which will be returned. When in data range,
            empty list will be returned.
        entryEnd -- Defines the end of the returned user data. Is not included. When
            it's larger or smaller than data, all data points beginning with
            entryBeginn will be returned.
        sortBy -- 0 => Sort by voice + text
            1 => Sort by voice
            2 => Sort by textcount
        """
        l = len(self.db)
        if entryBegin >= l:
            return []
        if entryEnd > l:
            entryEnd = l
        return self.sortDataBy(sortBy)[entryBegin:entryEnd]

    def addNewDataEntry(self, userID: int | str):
        """
        Adds a new data entry with the userID.

        Format of new data entry:
            {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": float,
                "Level": 0
            }

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        if not self.isInData(userID):
            t = time.time() - 60
            self.db[str(userID)] = {
                "Voice": 0,
                "Text": 0,
                "TextCount": 0,
                "Cooldown": t,
                "Level": 0,
            }
            print(f"\tCreated userID-Entry: {userID, self.db[str(userID)]}")

    def removeUserFromData(self, userID: int | str) -> bool:
        """
        Removes user entry with userID from userdata.json if it exists.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.

        return -- True if userID was in the database.
        """
        if not self.isInData(userID):
            return False
        del self.db[str(userID)]
        return True

    def addTextMindCooldown(
        self, userID: int | str, amount: int, cooldown: int | str | float
    ):
        """
        Adds XP for user in userdata.json by the amount in amount. Only add if user
        is not on cooldown.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        amount -- How much XP will be added as an int. Also negative numbers are
            possible to remove XP.
        cooldown -- How long a user needs to wait before being able to get XP.
        """
        self.addNewDataEntry(userID)
        cooldownTime = self.getCooldown(userID)
        self.addUserTextCount(userID)
        t = time.time()
        delta_t = t - float(cooldownTime)
        # Check if cooldown is up
        if delta_t >= float(cooldown):
            # Add XP
            self.addUserText(userID, amount)
            self.setCooldown(userID, t=t)
            print(f"\tUser {userID} gained {amount} TextXP")
        else:
            print(f"\tUser {userID} is on Cooldown. CurrentTime: {delta_t}")

    def addTextXP(self, userID: int | str, amount: int):
        """
        Adds XP for user in userdata.json by the amount in amount. Only add if user
        is not on cooldown of Texts.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        amount -- How much XP will be added as an int. Also negative numbers are
            possible to remove XP.
        """
        cooldown = self.ch.getFromConfig("textCooldown")
        self.addTextMindCooldown(userID, amount, cooldown)

    def addReactionXP(self, userID: int | str, amount: int | str):
        """
        Adds XP for user in userdata.json by the amount in amount. Only add if user
        is not on cooldown for Reactions.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        amount -- How much XP will be added as an int. Also negative numbers are
            possible to remove XP.
        """
        self.addTextMindCooldown(userID, amount, 10)

    def updateLevel(self, userID: int | str, level: int | str):
        """
        Sets user level to level if he is in userdata.json.

        Keyword arguments:
        userID -- Is the userID from discord user as a String or int
        level -- Integer which level the user should get.
        """
        if self.isInData(userID):
            entry = self.db[str(userID)]
            entry["Level"] = int(level)
            self.db[str(userID)] = entry

    def addAllUserVoice(self, userIDs: Iterable[int | str]):
        """
        Increments the voice XP of all users in userIDs by 1.
        If user not in userdata.json, than a new user entry will be added.

        Keyword arguments:
        userIDs -- Is a list of user IDs from discord user as a string or int.
        """
        for userID in userIDs:
            self.addUserVoice(userID)

    def addAllUserText(self, userIDs: Iterable[int | str], amount: int | str = 1):
        """
        Increments the text XP of all users in userIDs by amount.
        If user not in userdata.json, a new user entry will be added.

        Keyword arguments:
        userIDs -- Is a list of user IDs from discord user as a string or int.
        amount -- How much XP should be given. (Default: 1)
        """
        for userID in userIDs:
            self.addUserText(userID, amount)

    def getUserText(self, userID: int | str) -> int:
        """
        Gets the text from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        """
        return int(self.db[str(userID)]["Text"])

    def getUserVoice(self, userID: int | str) -> int:
        """
        Gets the voice from userdata.json for user with userID.

        Keyword arguments:
        userID:   Is the user ID from discord user as a string or int
        """
        return int(self.db[str(userID)]["Voice"])

    def getUserHours(self, userID: int | str) -> float:
        """
        Gets the Hours from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        return UserHandle.voiceToHours(self.getUserVoice(str(userID)))

    def getUserTextCount(self, userID: int | str) -> int:
        """
        Gets the TextCount from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        """
        return int(self.db[str(userID)]["TextCount"])

    def getCooldown(self, userID: int | str) -> float:
        """
        Gets the cooldown from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        return float(self.db[str(userID)]["Cooldown"])

    def getUserLevel(self, userID: int | str) -> int:
        """
        Keyword arguments:
        userID:   Is the user ID from discord user as a string or int

        Gets the level from userdata.json for user with userID.
        """
        return int(self.db[str(userID)]["Level"])

    def getUserIDsInData(self) -> Iterable[int]:
        """
        Gets the userIDs in userdata.json.
        """
        return map(int, self.db.keys())

    def setCooldown(self, userID: int | str, t: float | str | int = time.time()):
        """
        Sets the cooldown of a user in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        t -- Time to set the cooldown to. Default current time.
        """
        if self.isInData(userID):
            entry = self.db[str(userID)]
            entry["Cooldown"] = float(t)
            self.db[str(userID)] = entry

    def setUserVoice(self, userID: int | str, voice: int | str):
        """
        Sets a users Voice to voice in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        voice -- Integer to which the voice of a user is set to.
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["Voice"] = int(voice)
        self.db[str(userID)] = entry

    def setUserText(self, userID: int | str, text: str | int):
        """
        Sets the users text to text in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        text -- Integer to which the Text is set to.
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["Text"] = int(text)
        self.db[str(userID)] = entry

    def setUserTextCount(self, userID: int | str, textCount: int | str):
        """
        Sets the users text count to textCount in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        textCount -- Integer to which the text count is set to.
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["TextCount"] = int(textCount)
        self.db[str(userID)] = entry

    def addUserVoice(self, userID: int | str, voice: int | str = 1):
        """
        Adds voice to the users Voice in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        voice -- Integer to which is added to voice. Default is 1.
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["Voice"] = int(entry["Voice"]) + int(voice)
        self.db[str(userID)] = entry
        self.tempLeaderboard.addEntry(userID, XPTypes.VOICE, int(voice))

    def addUserText(self, userID: int | str, text: str | int):
        """
        Adds text to the users text in userdata.json.

        Keyword arguments:
        userID --Is the user ID from discord user as a string or int
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["Text"] = int(entry["Text"]) + int(text)
        self.db[str(userID)] = entry
        self.tempLeaderboard.addEntry(userID, XPTypes.TEXT, int(text))

    def addUserTextCount(self, userID: int | str, count: int | str = 1):
        """
        Adds count to the users TextCount in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        voice -- Integer to which is added to Voice. Default is 1.
        """
        self.addNewDataEntry(userID)
        entry = self.db[str(userID)]
        entry["TextCount"] = int(entry["TextCount"]) + int(count)
        self.db[str(userID)] = entry
        self.tempLeaderboard.addEntry(userID, XPTypes.TEXTCOUNT, int(count))

    @staticmethod
    def voiceToHours(voice: int) -> int:
        return round(voice / 30.0, 1)

    @classmethod
    def _cleanup(cls, db):
        """
        Method closing the database file, when the object is destroyed.
        Is defined to be executed in the constructor with 'atexit'.

        Keyword arguments:
        db -- SqliteDict database object, which should be closed.
        """
        print("[UserHandle] Closing Databank")
        db.commit()
        db.close()
