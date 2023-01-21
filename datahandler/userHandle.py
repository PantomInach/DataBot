import json
import os
import time

from typing import Callable, Any, Tuple, Iterable, Optional
from datahandler.configHandle import ConfigHandle


class UserHandle(object):
    """
    Handles manipulation and reading from userdata.json
    """

    _instance = None

    def __new__(cls):
        """Singelton pattern."""
        if cls._instance is None:
            cls._instance = super(UserHandle, cls).__new__(cls)
            cls.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
            # Reads in userdata.json
            cls.data = json.load(open(cls.datapath + "userdata.json"))
            cls.ch = ConfigHandle()
        return cls._instance

    """
        Functions to manipulate the userdata.json
    """

    def _reloadData(func: Callable[["UserHandle", Any], Any]):
        """
        Type:   Decorator for functions in UserHandle using self.data

        Reloads the data file and executes the function.
        Mitigates race conditions and data corruption when creating multiple
        UserHandle objects.
        """

        def decorator(self, *args, **kwargs):
            self.data = json.load(open(self.datapath + "userdata.json"))
            return func(self, *args, **kwargs)

        return decorator

    @_reloadData
    def isInData(self, userID: Any) -> bool:
        """
        Tests if the user has an entry in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        return str(userID) in self.data.keys()

    @_reloadData
    def sortDataBy(self, sortBy: int):
        """
        Sorts userdata.json depending on sortBy.

        Keyword arguments:
        sortBy -- 0 => Sort by voice + text
            1 => Sort by voice
            2 => Sort by textcount
        """
        sortMode = [[1, 1, 0], [0, 1, 0], [0, 0, 1]]
        sortedData = sorted(
            self.data,
            key=lambda id: sortMode[sortBy][0] * self.getUserText(id)
            + sortMode[sortBy][1] * self.getUserVoice(id)
            + sortMode[sortBy][2] * self.getUserTextCount(id),
        )
        return sortedData[::-1]

    @_reloadData
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
        l = len(self.data)
        if entryBegin >= l:
            return []
        if entryEnd > l:
            entryEnd = l
        return self.sortDataBy(sortBy)[entryBegin:entryEnd]

    @_reloadData
    def addNewDataEntry(self, userID: Any):
        """

        Adds a new data entry with the userID.

        Format of new data entry:
            {
                "Voice": "0",
                "Text": "0",
                "TextCount": "0",
                "Cooldown": float,
                "Level": "0"
            }

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        if not self.isInData(userID):
            t = time.time() - 60
            self.data[str(userID)] = {
                "Voice": "0",
                "Text": "0",
                "TextCount": "0",
                "Cooldown": t,
                "Level": "0",
            }
            print(f"\tCreated userID-Entry: {userID, self.data[str(userID)]}")
            self.saveData()

    @_reloadData
    def removeUserFromData(self, userID: Any) -> bool:
        """
        Removes user entry with userID from userdata.json if it exists.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        if not self.isInData(userID):
            return False
        del self.data[str(userID)]
        self.saveData()
        return True

    @_reloadData
    def addTextMindCooldown(self, userID: Any, amount: int, cooldown: Any):
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
        cooldownTime = self.data[str(userID)]["Cooldown"]
        cooldownCon = cooldown
        self.addUserTextCount(userID)
        t = time.time()
        deltat = t - float(cooldownTime)
        # Check if cooldown is up
        if deltat >= float(cooldownCon):
            # Add XP
            self.addUserText(userID, amount)
            self.setCooldown(userID, t=t)
            print(f"\tUser {userID} gained {amount} TextXP")
        else:
            print(f"\tUser {userID} is on Cooldown. CurrentTime: {deltat}")
        self.saveData()

    @_reloadData
    def addTextXP(self, userID: Any, amount: Any):
        """
        Adds XP for user in userdata.json by the amount in amount. Only add if user
        is not on cooldown of Texts.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        amount -- How much XP will be added as an int. Also negative numbers are
            possible to remove XP.
        """
        cooldownCon = self.ch.getFromConfig("textCooldown")
        self.addTextMindCooldown(userID, amount, cooldownCon)
        self.saveData()

    @_reloadData
    def addReactionXP(self, userID: Any, amount: Any):
        """
        Adds XP for user in userdata.json by the amount in amount. Only add if user
        is not on cooldown for Reactions.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        amount -- How much XP will be added as an int. Also negative numbers are
            possible to remove XP.
        """
        self.addTextMindCooldown(userID, amount, 10)
        self.saveData()

    @_reloadData
    def updateLevel(self, userID: Any, level: Any):
        """
        Sets user level to level if he is in userdata.json.

        Keyword arguments:
        userID -- Is the userID from discord user as a String or int
        level -- Integer which level the user should get.
        """
        if self.isInData(userID):
            self.data[str(userID)]["Level"] = level
            self.saveData()

    @_reloadData
    def addAllUserVoice(self, userIDs: Iterable[Any]):
        """
        Increments the voice XP of all users in userIDs by 1.
        If user not in userdata.json, than a new user entry will be added.

        Keyword arguments:
        userIDs -- Is a list of user IDs from discord user as a string or int.
        """
        for userID in userIDs:
            self.addUserVoice(userID)

    @_reloadData
    def addAllUserText(self, userIDs: Iterable[Any], amount=1):
        """
        Increments the text XP of all users in userIDs by amount.
        If user not in userdata.json, a new user entry will be added.

        Keyword arguments:
        userIDs -- Is a list of user IDs from discord user as a string or int.
        amount -- How much XP should be given. (Default: 1)
        """
        for userID in userIDs:
            self.addUserText(userID, amount)

    @_reloadData
    def getUserText(self, userID: Any) -> int:
        """
        Gets the text from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        """
        return int(self.data[str(userID)]["Text"])

    @_reloadData
    def getUserVoice(self, userID: Any) -> int:
        """
        Gets the voice from userdata.json for user with userID.

        Keyword arguments:
        userID:   Is the user ID from discord user as a string or int
        """
        return int(self.data[str(userID)]["Voice"])

    @_reloadData
    def getUserHours(self, userID: Any) -> float:
        """
        Gets the Hours from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        return round(self.getUserVoice(userID) / 30.0, 1)

    @_reloadData
    def getUserTextCount(self, userID: Any) -> int:
        """
        Gets the TextCount from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        """
        return int(self.data[str(userID)]["TextCount"])

    @_reloadData
    def getCooldown(self, userID: Any):
        """
        Gets the cooldown from userdata.json for user with userID.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        """
        if self.isInData(userID):
            return self.data[str(userID)]["Cooldown"]

    @_reloadData
    def getUserLevel(self, userID: Any) -> Optional[int]:
        """
        Keyword arguments:
        userID:   Is the user ID from discord user as a string or int

        Gets the level from userdata.json for user with userID.
        """
        if self.isInData(userID):
            return int(self.data[str(userID)]["Level"])
        return None

    @_reloadData
    def getUserIDsInData(self):
        """
        Gets the userIDs in userdata.json.
        """
        return self.data.keys()

    @_reloadData
    def setCooldown(self, userID: Any, t=time.time()):
        """
        Sets the cooldown of a user in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        t -- Time to set the cooldown to. Default current time.
        """
        if self.isInData(userID):
            self.data[str(userID)]["Cooldown"] = str(t)
            self.saveData()

    @_reloadData
    def setUserVoice(self, userID: Any, voice: int):
        """
        Sets a users Voice to voice in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        voice -- Integer to which the voice of a user is set to.
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["Voice"] = int(voice)
        self.saveData()

    @_reloadData
    def setUserText(self, userID: Any, text: str):
        """
        Sets the users text to text in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        text -- Integer to which the Text is set to.
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["Text"] = int(text)
        self.saveData()

    @_reloadData
    def setUserTextCount(self, userID: Any, textCount: int):
        """
        Sets the users text count to textCount in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        textCount -- Integer to which the text count is set to.
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["TextCount"] = int(textCount)
        self.saveData()

    @_reloadData
    def addUserVoice(self, userID: Any, voice=1):
        """
        Adds voice to the users Voice in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        voice -- Integer to which is added to voice. Default is 1.
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["Voice"] = int(self.data[str(userID)]["Voice"]) + int(
            voice
        )
        self.saveData()

    @_reloadData
    def addUserText(self, userID: Any, text: str):
        """
        Adds text to the users text in userdata.json.

        Keyword arguments:
        userID --Is the user ID from discord user as a string or int
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["Text"] = int(self.data[str(userID)]["Text"]) + int(text)
        self.saveData()

    @_reloadData
    def addUserTextCount(self, userID: Any, count=1):
        """
        Adds count to the users TextCount in userdata.json.

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int.
        voice -- Integer to which is added to Voice. Default is 1.
        """
        self.addNewDataEntry(userID)
        self.data[str(userID)]["TextCount"] = int(
            self.data[str(userID)]["TextCount"]
        ) + int(count)
        self.saveData()

    def saveData(self):
        """
        Saves current userdata.json to disc and reads it again.
        """
        with open(self.datapath + "userdata.json", "w") as f:
            json.dump(self.data, f, indent=6)
        self.data = json.load(open(self.datapath + "userdata.json"))
