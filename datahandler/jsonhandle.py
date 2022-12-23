import json
import os
import time

from typing import Callable, Any, Tuple, Iterable, Optional


class Jsonhandle(object):
    """
    Handles manipulation and reading from userdata.json and config.json
    """

    _instance = None

    def __new__(cls):
        """Singelton pattern."""
        if cls._instance is None:
            cls._instance = super(Jsonhandle, cls).__new__(cls)
            cls.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
            # Reads in userdata.json and config.json
            cls.config = json.load(open(cls.datapath + "config.json"))
            cls.data = json.load(open(cls.datapath + "userdata.json"))
        return cls._instance

    """
    ###########################################
    Part: config
        Functions to manipulate the config json
    """

    def _reloadConfig(func: Callable[["Jsonhandle", Any], Any]):
        """
        Reloads the config file and executes the function.
        Mitigates race conditions and data corruption when creating multiple
        Jsonhandel objects.

        Type:   Decorator for functions in Jsonhandel using self.config
        """

        def decorator(self, *args, **kwargs):
            self.config = json.load(open(self.datapath + "config.json"))
            return func(self, *args, **kwargs)

        return decorator

    @_reloadConfig
    def isInConfig(self, isIn: str) -> bool:
        """
        Tests if isIn is in config.

        Keyword arguments:
        isIn -- String or integer which may be in config.json.
        """
        return isIn in self.config.keys()

    @_reloadConfig
    def getFromConfig(self, toGet: str):
        """
        Get Values from config file.

        Keyword arguments:
        toGet -- Reads String or integer from config.json
        """
        return self.config[str(toGet)]

    @_reloadConfig
    def getPrivilegeLevel(self, userID: Any) -> int:
        """
        Gives back the privilege level of userID
                Level 0:    User
                Level 1:    Mod
                Level 2:    Owner

        Keyword arguments:
        userID -- Is the user ID from discord user as a string or int
        """
        if str(userID) in [x for x in self.config["privilege"]]:
            return int(self.config["privilege"][str(userID)])
        return 0

    @_reloadConfig
    def getInPrivilege(self) -> Tuple[Any, ...]:
        """
        Get userIDs with there privilege level in config.json.
        """
        return tuple(self.config["privilege"].keys())

    def saveConfig(self):
        """
        Saves config.json and reads it in again.
        """
        with open(self.datapath + "config.json", "w") as f:
            json.dump(self.config, f, indent=6)
        self.config = json.load(open(self.datapath + "config.json"))

    @_reloadConfig
    def getRoles(self):
        """
        Get from config.json the rolls which the bot will give depending on the users
        XP.
        """
        return self.config["roles"]

    @_reloadConfig
    def getRolesXPNeed(self):
        """
        Gets which level is needed for each role.
        """
        return self.config["rolesXPNeed"]

    def get_subserver_needed_roles(self):
        """
        Gets every role needed for a member to use a sub server
        """
        return self.config["needForSubServer"]

    def get_guild(self) -> int:
        """
        Gets the guild ID as an integer
        """
        return int(self.config["guild"])

    """
    ##########
    channel black- and whitelist
    """

    @_reloadConfig
    def isInBlacklist(self, channelID: Any) -> bool:
        """
        Test if he channelID is in the blacklist of the config.json.

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.
        """
        return str(channelID) in self.config["serverVoiceBlacklist"].keys()

    @_reloadConfig
    def writeToBalcklist(self, channelID: Any) -> bool:
        """
        Stores the channelID in config.json in the blacklist list.

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.

        return -- False if channel is already in the blacklist. Else True.
        """
        if self.isInBlacklist(channelID):
            return False
        self.config["serverVoiceBlacklist"].append(str(channelID))
        self.saveConfig()
        return True

    @_reloadConfig
    def removeFromBalcklist(self, channelID: Any) -> bool:
        """
        Removes the channelID from the blacklist in config.json

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.

        return -- False if channel is not in blacklist. Else True.
        """
        if not self.isInBlacklist(channelID):
            return False
        self.config["serverVoiceBlacklist"].remove(str(channelID))
        self.saveConfig()
        return True

    @_reloadConfig
    def isInWhitelist(self, channelID: Any) -> bool:
        """
        Test if channelID is in whitelist in config.json

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.
        """
        return str(channelID) in self.config["serverTextWhitelist"].keys()

    @_reloadConfig
    def writeToWhitelist(self, channelID: Any) -> bool:
        """
        Stores the channelID in config.json in the whitelist list.

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.

        return -- False if channel is in whitelist. Else True.
        """
        if self.isInWhitelist(channelID):
            return False
        self.config["serverTextWhitelist"].append(str(channelID))
        self.saveConfig()
        return True

    @_reloadConfig
    def removeFromWhitelist(self, channelID: Any) -> bool:
        """
        Removes the channelID from the whitelist in config.json

        Keyword arguments:
        channelID -- The ID of the channel the message of messageID is in.

        return -- True if channel is in whitelist. Else False.
        """
        if not self.isInWhitelist(channelID):
            return False
        self.config["serverTextWhitelist"].remove(str(channelID))
        self.saveConfig()
        return True

    def get_token(self) -> str:
        """
        Gets the token from the config file
        !!! WARNING !!! Leaking the token can lead to a takeover of the bot
        """
        return self.config["token"]

    """
    ###########################################
    Part: Data
        Functions to manipulate the userdata.json
    """

    def _reloadData(func: Callable[["Jsonhandle", Any], Any]):
        """
        Type:   Decorator for functions in Jsonhandel using self.config

        Reloads the data file and executes the function.
        Mitigates race conditions and data corruption when creating multiple
        Jsonhandel objects.
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
        cooldownCon = self.getFromConfig("textCooldown")
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
        self.data[str(userID)]["Text"] = int(
            self.data[str(userID)]["Text"]) + int(text)
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
