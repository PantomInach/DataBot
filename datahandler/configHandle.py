import json
import os
import time

from typing import Callable, Any, Tuple, Iterable, Optional


class ConfigHandle(object):
    """
    Handles manipulation and reading from config.json
    """

    _instance = None

    def __new__(cls):
        """Singelton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigHandle, cls).__new__(cls)
            cls.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/"
            # Reads in config.json
            with open(cls.datapath + "config.json", "r") as f:
                cls.config = json.load(f)
        return cls._instance

    """
        Functions to manipulate the config json
    """

    def _reloadConfig(func: Callable[["ConfigHandle", Any], Any]):
        """
        Reloads the config file and executes the function.
        Mitigates race conditions and data corruption when creating multiple
        ConfigHandle objects.

        Type:   Decorator for functions in ConfigHandle using self.config
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
        return str(channelID) in self.config["serverVoiceBlacklist"]

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
        return str(channelID) in self.config["serverTextWhitelist"]

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
