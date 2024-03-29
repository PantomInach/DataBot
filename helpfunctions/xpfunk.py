import random

from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle


class Xpfunk(object):
    """
    Class calculates XP specific operations.
    """

    def __init__(self):
        """
        param ch:	ConfigHandle object passed when created.
        param uh:   UserHandle object passed when created.

        Creates object.
        """
        super(Xpfunk, self).__init__()
        # Read only
        self.ch = ConfigHandle()
        self.uh = UserHandle()

    def textXP(self, message):
        """
        param message:	String which length determines how much XP will be given
        """
        if len(message) >= 150:
            return random.randint(20, 40)
        return random.randint(15, 25)

    def randomRange(self, start, end):
        """
        param start:	int
        param end:		int

        Gives random integer in range [start, end[.
        """
        return random.randint(start, end)

    def giveXP(self, voice, text):
        """
        param voice:	int
        param text:		int

        Gives member XP by voice and text.
        """
        return voice + text

    def levelRoleList(self, userID):
        """
        param userID:	Is the user ID from discord user as a string

        Returns all roles which user needs to have depending on his XP on the guild.
        """
        roles = self.ch.getRoles()
        rolesXPNeed = self.ch.getRolesXPNeed()
        roleList = []
        userLevel = int(self.uh.getUserLevel(userID))
        # Goes through all roles XP limits in the config file.
        for i in range(len(roles)):
            if userLevel >= rolesXPNeed(i):
                # Addes role
                roleList.append(roles[i])
            else:
                break
        return roleList

    def levelFunk(self, voice, text):
        """
        param voice:	int
        param text:		int

        Gives the level depending on given voice and text XP.
        """
        level = 0
        xp = int(voice) + int(text)
        levelLim = 100
        while xp > levelLim:
            level += 1
            levelLim += 100 + sum([(55 + y * 10) for y in range(level)])
        return int(level)

    def xpNeed(self, voice, text):
        """
        param voice:	int
        param text:		int

        Gives the XP limit for the XP level depending on the voice and text XP.
        """
        level = 0
        xp = int(voice) + int(text)
        levelLim = 100
        while xp > levelLim:
            level += 1
            levelLim += sum([(55 + y * 10) for y in range(level)]) + 100
        return levelLim
