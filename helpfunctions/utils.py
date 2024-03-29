import os
import datetime
import re
import math
from discord.utils import find
from discord.ui import View

from helpfunctions.xpfunk import Xpfunk
from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle
from datahandler.tempLeaderboard import XPTypes, TempLeaderboard

from button_views.leaderboard_buttons import LeaderboardButtons

# import hashlib

from emoji import UNICODE_EMOJI
from typing import Union, Dict, Tuple

NUMBER_OF_USERS_PER_PAGE = 10


class Utils(object):
    """
    This class holds multiple purpose commands for all classes.
    """

    def __init__(self, bot, ch=None, uh=None):
        """
        param bot:	commands.Bot object.
        param ch:	ConfigHandle object from datahandler.configHandle. When not given, a new instance will be created.
        param uh:	UserHandle object from datahandler.userHandle. When not given, a new instance will be created.
        """
        super(Utils, self).__init__()
        self.bot = bot
        self.ch = ch if ch else ConfigHandle()
        self.uh = uh if uh else UserHandle()
        self.xpf = Xpfunk()
        self.tempLeaderboard = TempLeaderboard()

    def hasRole(self, userID, role):
        """
        param userID:	Is the user ID from discord user as a string or int
        param role:		Which role to check. Needs to be the role's name or ID.

        Checks if a member has the role.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        return find(
            lambda r: r.name == role or r.id == role or str(r.id) == role,
            member.roles,
        )

    def hasRoles(self, userID, roles):
        """
        param userID:	Is the user ID from discord user as a string or int
        param role:		List of roles which to check for. Needs to be the role's name or ID.

        Checks if a member has all roles in roles.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        memberRoles = (
            set()
            .union({x.name for x in member.roles})
            .union({x.id for x in member.roles})
            .union({str(x.id) for x in member.roles})
        )
        return set(roles).issubset(memberRoles)

    def hasOneRole(self, userID, roles):
        """
        param userID:	Is the user ID from discord user as a string or int
        param roles:	List of roles which to check for. Needs to be the role's name or ID.

        Checks if a member has any one role of roles.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        return (
            sum(
                1
                for x in member.roles
                if x.id in roles or str(x.id) in roles or x.name in roles
            )
            >= 1
        )

    async def giveRole(self, userID, roleName):
        """
        param userID:	Is the user ID from discord user as a string or int
        param roleName:	Role to give. Needs to be the role's name or ID.

        Gives the member with userID the role roleName.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        role = find(
            lambda r: r.id == roleName or str(r.id) == roleName or r.name == roleName,
            guild.roles,
        )
        if role:
            await member.add_roles(role)
            await self.log(
                f"User {member.name} aka {member.nick} got role {roleName}.", 1
            )
        else:
            await self.log(f"[ERROR] In giveRole:\t Role {roleName} not found", 1)

    async def giveRoles(self, userID, roleNames):
        """
        param userID:	Is the user ID from discord user as a string or int
        param roleNames:	List of roles to give. Needs to be the role's name or ID.

        Gives the member with userID the roles roleNames.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        # Gets the roles to give by the role's name.
        rolesList = tuple(
            find(
                lambda role: str(role.id) == r or role.id == r or role.name == r,
                list(set(guild.roles) - set(member.roles)),
            )
            for r in roleNames
        )
        # Discard Discord None roles, which resulte in errors.
        rolesList = [x for x in rolesList if x != None]
        if len(rolesList) > 0:
            # Give roles
            await member.add_roles(*rolesList)
            # Get newly given roles for the message.
            await self.log(
                f"User {member.name} aka {member.nick} got roles {[role.name for role in rolesList]}.",
                1,
            )

    async def removeRole(self, userID, roleName):
        """
        param userID:	Is the user ID from discord user as a string or int
        param roleName:	Role to remove. Needs to be the role's name or ID.

        Removes the member with userID the role roleName.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        role = find(
            lambda r: r.id == roleName or str(r.id) == roleName or r.name == roleName,
            member.roles,
        )
        if role:
            await member.remove_roles(role)
            await self.log(
                f"User {member.name} aka {member.nick} got his role {roleName} removed.",
                1,
            )
        else:
            await self.log(f"[ERROR] In giveRole:\t Role {roleName} not found", 1)

    async def removeRoles(self, userID, roleNames, reason=None):
        """
        param userID:	Is the user ID from discord user as a string or int
        param roleNames:	List of roles to remove. Needs to be the role's name or ID.
        param reason:	Specify reason in AuditLog from guild. Default is None.

        Removes the member with userID the roles roleNames.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = guild.get_member(int(userID))
        # Gets the roles to remove by the role's name.
        rolesList = tuple(
            find(
                lambda role: str(role.id) == r or role.id == r or role.name == r,
                member.roles,
            )
            for r in roleNames
        )
        # Discord None roles, which result in errors.
        rolesList = [x for x in rolesList if x != None]
        memberRolesPrev = member.roles
        if len(rolesList) > 0:
            await member.remove_roles(*rolesList, reason=reason)
            # Get newly removed roles for message.
            rolesAfter = {
                role.name for role in memberRolesPrev if not role in member.roles
            }
            await self.log(
                f"User {member.name} aka {member.nick} got his roles {str(rolesAfter)} removed.",
                1,
            )

    @staticmethod
    def roundScientificUnitless(number: str | float | int) -> str:
        """
        Rounds input number to a value with 4 digits and uses symbols of the unit prefixes in the metric system to do so.

        Keyword arguments:
        number -- Is an random number as a string, float or int.
        """
        if len(str(number)) > 7:
            number = str(number)[:-6] + "M"
        elif len(str(number)) > 6:
            number = str(round(float(number) / 1000000, 1)) + "M"
        elif len(str(number)) > 4:
            number = str(number)[:-3] + "k"
        return number

    @staticmethod
    def roundScientificTime(hours: float) -> str:
        """
        Rounds input hours to a value never higher than 5 digits and uses symbols of the unit prefixes in the metric system to do so.

        Keyword arguments:
        hours -- Is an time value as a float.
        """
        if math.floor(hours) >= 24 * 1000:
            hours = str(round(hours / 24 / 365, 1)) + "a"
        elif math.floor(hours) >= 1000:
            hours = str(round(hours / 24, 1)) + "d"
        else:
            hours = str(hours) + "h"
        hours = (
            hours if len(hours) <= 5 else str(math.floor(float(hours[:-1]))) + hours[-1]
        )
        return hours

    def getTempLeaderboardPageBy(self, page, sortBy, timeFrame: int):
        """
        param page:	Which page of the leaderboard is shown. Begins with page 0. A page contains 10 entries by default.
        param sortBy:
                        0 => Sort by voice + text
                        1 => Sort by voice
                        2 => Sort by textcount
        param timeFrame: How far the temporary leaderboard should look back in days.

        Builds a string for the leaderboard on a given page with the right sorting.
        """
        userPerPage = NUMBER_OF_USERS_PER_PAGE
        firstUserOnLeaderBoard = page * userPerPage
        userIDs: Tuple[
            Tuple[str, Dict[XPTypes, int]]
        ] = self.tempLeaderboard.sortDataWindowBy(sortBy, window=timeFrame)[
            firstUserOnLeaderBoard : firstUserOnLeaderBoard + userPerPage
        ]
        rank = page * userPerPage + 1
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        leaderboard = (
            f"**Leaderboard {guild.name} of the last {timeFrame} days**\n```as"
        )
        # Generate leaderboard string
        if not userIDs:
            return ""
        for userID, value in userIDs:
            nick, name = Utils._getUserNameNickCombo(userID, guild)
            # Formatting data
            other, voice, text, textcount, *_ = value.values()
            hours = Utils.roundScientificTime(UserHandle.voiceToHours(voice))
            messages = Utils.roundScientificUnitless(textcount)
            xp = Utils.roundScientificUnitless(self.xpf.giveXP(voice, text))
            # Formatting for leaderboard.
            leaderboard += f"\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(28-len(nick+name))}({name})   TIME: {' '*(5-len(str(hours)))}{hours}   TEXT: {' '*(4-len(str(messages)))}{messages}   EXP: {' '*(4-len(str(xp)))}{xp}\n"
            rank += 1
        leaderboard += f"```"
        return leaderboard

    def getLeaderboardPageBy(self, page, sortBy):
        """
        param page:	Which page of the leaderboard is shown. Begins with page 0. A page contains 10 entries by default.
        param sortBy:
                        0 => Sort by voice + text
                        1 => Sort by voice
                        2 => Sort by textcount

        Builds a string for the leaderboard on a given page with the right sorting.
        """
        user_per_page = NUMBER_OF_USERS_PER_PAGE
        userIDs = self.uh.getSortedDataEntrys(
            page * user_per_page, (page + 1) * user_per_page, sortBy
        )
        rank = page * user_per_page + 1
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        leaderboard = f"**Leaderboard {guild.name}**\n```as"
        # Generate leaderboard string
        if not userIDs:
            return ""
        for userID in userIDs:
            nick, name = Utils._getUserNameNickCombo(userID, guild)
            # Get user data from userdata.json.
            hours = self.uh.getUserHours(userID)
            messages = self.uh.getUserTextCount(userID)
            xp = self.xpf.giveXP(
                self.uh.getUserVoice(userID), self.uh.getUserText(userID)
            )
            level = self.uh.getUserLevel(userID)
            # Formatting data
            hours = Utils.roundScientificTime(hours)
            messages = Utils.roundScientificUnitless(messages)
            xp = Utils.roundScientificUnitless(xp)
            # Formatting for leaderboard.
            leaderboard += f"\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(28-len(nick+name))}({name})   TIME: {' '*(5-len(str(hours)))}{hours}   TEXT: {' '*(4-len(str(messages)))}{messages}   EXP: {' '*(4-len(str(xp)))}{xp}   LVL: {' '*(3-len(str(level)))}{level}\n"
            rank += 1
        leaderboard += f"```"
        return leaderboard

    @staticmethod
    def _get_leaderboard_pageFirstRank(leaderboard_page: str) -> int:
        """
        param leaderboard_page:	String of a page of leaderboard.

        Determines the first rank number on leaderboard page. Used to identify the number of the current page.
        """
        leaderboard_search_pattern = re.compile("```as\n *[0-9]+\.")
        leaderboard_search_match = leaderboard_search_pattern.search(
            str(leaderboard_page)
        )
        # Check if match was found.
        leaderboard_search_result = (
            "" if not leaderboard_search_match else leaderboard_search_match.group(0)
        )
        pageFirstRank = int(str(leaderboard_search_result)[6:-1])
        return pageFirstRank

    @staticmethod
    def getMessageState(
        message, view: Union[None, View, LeaderboardButtons, object] = None
    ):
        """
        param message:	String of a message in Discord.

        Determines in which state the message is. Used to identify Bot features such as leaderbord or polls.

        State (0,0): Normal Message
        State (1,x): Leaderboard sorted by XP on page x
        State (2,x): Leaderboard sorted by Voice on page x
        State (3,x): Leaderboard sorted by TextCount on page x
        State (4,0): Poll
        State (5,0): Data protection declaration
        State (6,0): GiveRoles message
        """
        if not message.author.bot:
            return (0, 0)

        # Some features relay on the reactions to identify them. For example the leaderboard.
        reactions = message.reactions
        reactionstr = ""
        textBeginn = message.content[:5]
        for reaction in reactions:
            reactionstr += str(reaction)
        state = 0

        # Check for leaderboard
        if view and isinstance(view, LeaderboardButtons):
            state = view.sorted_by.value + 1

        # Check for poll via the start of the message string.
        elif textBeginn == "```md" and reactionstr[0:2] == "1⃣":
            return (4, 0)

        # Check for data protection declaration.
        elif textBeginn == "**Not":
            return (5, 0)

        # Check for give roles message.
        elif textBeginn == "**Cho":
            return (6, 0)

        # Normal message or not implemented yet.
        else:
            return (0, 0)

        # Is leaderboard and now find the page of it.
        pageFirstRank = Utils._get_leaderboard_pageFirstRank(message.content)
        return (state, pageFirstRank // NUMBER_OF_USERS_PER_PAGE)

    async def sendServerModMessage(self, string, embed=None):
        """
        param string:	String which is send.
        Sends all Mods on the guild string.
        !!! Not modular and sends it to COO !!!
        """
        server = self.bot.get_guild(int(self.uh.getFromConfig("guild")))
        for user in server.members:
            if self.hasRole(user.id, "COO"):
                await user.send(string, embed=embed)

    async def sendModsMessage(self, string, embed=None):
        """
        param string:	String which will be sent.

        Sends all Mods of the Bot with privilege level of 1 or higher the string.
        """
        await self.sendMessageToPrivilage(string, 1, embed=embed)

    async def sendOwnerMessage(self, string, embed=None):
        """
        param string:	String which is send.

        Sends all Owners of the Bot with privilege level of 2 or higher the string.
        """
        await self.sendMessageToPrivilage(string, 2, embed=embed)

    async def sendMessageToPrivilage(self, string, level, embed=None):
        """
        param string:	String which is send.
        param level:	Integer of the minimum level.

        Sends all Users of the Bot with privilege level of level or higher the string.
        """
        for x in self.ch.getInPrivilege():
            if self.ch.getPrivilegeLevel(x) >= level:
                user = self.bot.get_user(int(x))
                await user.send(string, delete_after=604800, embed=embed)

    async def log(self, message, level):
        """
        param message:	String to write to log.txt.
        param level:	Sends to whom level is high enough.

        Saves a message to the log.txt and messages all Users with a privilege level of level or higher.
        """
        message = str(datetime.datetime.now()) + ":\t" + message
        # Send message
        await self.sendMessageToPrivilage(message, level)
        # Log to log.
        Utils.logToFile(message)
        print(message)

    @staticmethod
    def logToFile(message, withDate=False):
        """
        param message:	String to write to log.txt.

        Writes message to log.txt
        """
        if withDate:
            message = str(datetime.datetime.now()) + ":\n" + message
        message = "\n" + message
        logfile = str(os.path.dirname(os.path.dirname(__file__))) + "/data/log.txt"
        with open(logfile, "a") as l:
            l.write(f"{message}\n")

    @staticmethod
    def _getUserNameNickCombo(userID: int | str, guild) -> (str, str):
        member = guild.get_member(int(userID))
        # When user is not in guild, member is None.
        if member is not None:
            # Filter out Emojis in names
            nick = "".join(
                [c for c in member.display_name if c not in UNICODE_EMOJI["en"]]
            )
            name = "".join([c for c in member.name if c not in UNICODE_EMOJI["en"]])
        else:
            # When user is not in guild.
            nick = "-X-"
            name = f"ID: {userID}"
        # Check length of nick + name
        nick = nick if len(nick) <= 12 else nick[:9] + "..."
        name = name if len(name + nick) <= 25 else name[: 22 - len(nick)] + "..."
        return (nick, name)

    def getUH(self):
        """
        Returns the UserHandle object in self.uh.
        """
        return self.uh

    def getCH(self):
        """
        Returns the ConfigHandle object in self.ch.
        """
        return self.ch

    """
	Unsupported
	
	def hashData(self, voice, text, textCount, userID):
		code = self.xpf.randomRange(100000, 999999)
		return self.hashDataWithCode(voice, text, textCount, userID, code)

	def hashDataWithCode(self, voice, text, textCount, userID, code):
		stage1 = [int(voice) ^ int(text) ^ int(code), int(text) ^ int(textCount) ^ int(code), int(textCount) ^ int(userID) ^ int(code)]
		stage2 = [hashlib.sha256(str(i).encode()).hexdigest() for i in stage1]
		re = ""
		for s in stage2:
			re = re.join(s)
		re = hashlib.sha256(str(re).encode()).hexdigest()
		return [re, code]
	"""
