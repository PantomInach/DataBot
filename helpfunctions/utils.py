import discord
from discord.utils import get, find
from discord.ext import commands
import os
import datetime

from helpfunctions.xpfunk import Xpfunk
from datahandler.jsonhandel import Jsonhandel
# import hashlib

from emoji import UNICODE_EMOJI

class Utils(object):
	"""
	This class holds multiple purpose commands for all classes.
	"""
	def __init__(self, bot, jh = None):
		"""
		param bot:	commands.Bot object.
		param jh:	Jsonhandel object from datahandler.jsonhandel. When not given, a new instance will be created.
		"""
		super(Utils, self).__init__()
		self.bot = bot
		self.jh = jh if jh else Jsonhandel()
		self.xpf = Xpfunk()

	def hasRole(self, userID, role):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param role:		Which role to check. Needs to be the role's name or ID.

		Checks if a member has the role.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		return find(lambda r: r.name == role or r.id == role or str(r.id) == role, member.roles)

	def hasRoles(self, userID, roles):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param role:		List of roles which to check for. Needs to be the role's name or ID.

		Checks if a member has all roles in roles.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		memberRoles = set().union({x.name for x in member.roles}).union({x.id for x in member.roles}).union({str(x.id)for x in member.roles})
		return set(roles).issubset(memberRoles)

	def hasOneRole(self, userID, roles):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param roles:	List of roles which to check for. Needs to be the role's name or ID.

		Checks if a member has any one role of roles.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		return len({x for x in member.roles if x.id in roles or str(x.id) in roles or x.name in roles}) >= 1

	async def giveRole(self, userID, roleName):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param roleName:	Role to give. Needs to be the role's name or ID.

		Gives the member with userID the role roleName.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		role = find(lambda r: r.id == roleName or str(r.id) == roleName or r.name == roleName, guild.roles)
		if role:
			await member.add_roles(role)
			await self.log(f"User {member.name} aka {member.nick} got role {roleName}.",1)
		else:
			await self.log(f"[ERROR] In giveRole:\t Role {roleName} not found", 1)

	async def giveRoles(self, userID, roleNames):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param roleNames:	List of roles to give. Needs to be the role's name or ID.

		Gives the member with userID the roles roleNames.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		# Gets the roles to give by the role's name.
		rolesList = tuple(find(lambda role: str(role.id) == r or role.id == r or role.name == r, list(set(guild.roles)-set(member.roles))) for r in roleNames)
		# Discard Discord None roles, which resulte in errors.
		rolesList = [x for x in rolesList if x != None]
		if len(rolesList) > 0:
			# Give roles
			await member.add_roles(*rolesList)
			# Get newly given roles for message.
			await self.log(f"User {member.name} aka {member.nick} got roles {[role.name for role in rolesList]}.",1)

	async def removeRole(self, userID, roleName):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param roleName:	Role to remove. Needs to be the role's name or ID.

		Removes the member with userID the role roleName.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		role = find(lambda r: r.id == roleName or str(r.id) == roleName or r.name == roleName, member.roles)
		if role:
			await member.remove_roles(role)
			await self.log(f"User {member.name} aka {member.nick} got his role {roleName} removed.",1)
		else:
			await self.log(f"[ERROR] In giveRole:\t Role {roleName} not found",1)

	async def removeRoles(self, userID, roleNames, reason = None):
		"""
		param userID:	Is the user ID from discord user as a string or int
		param roleNames:	List of roles to remove. Needs to be the role's name or ID.
		param reason:	Specify reason in AuditLog from guild. Default is None.

		Removes the member with userID the roles roleNames.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		member = guild.get_member(int(userID))
		# Gets the roles to remove by the role's name.
		rolesList = tuple(find(lambda role: str(role.id) == r or role.id == r or role.name == r, member.roles) for r in roleNames)
		# Discord None roles, which result in errors.
		rolesList = [x for x in rolesList if x != None]
		memberRolesPrev = member.roles
		if len(rolesList) > 0:
			await member.remove_roles(*rolesList, reason = reason)
			# Get newly removed roles for message.
			rolesAfter = {role.name for role in memberRolesPrev if not role in member.roles}
			await self.log(f"User {member.name} aka {member.nick} got his roles {str(rolesAfter)} removed.",1)

	def getLeaderboardPageBy(self, page, sortBy):
		"""
		param page:	Which page of the leaderboard is shown. Begins with page 0. A page contains 10 entries by default.
		param sortBy:
				0 => Sort by voice + text
				1 => Sort by voice
				2 => Sort by textcount
		
		Builds a string for the leaderboard on a given page with the right sorting.
		"""
		userIDs = self.jh.getSortedDataEntrys(page*10, (page+1)*10 ,sortBy)
		leaderborad = ""
		rank = page*10+1
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		# Generate leaderboard string
		for userID in userIDs:
			member = guild.get_member(int(userID))
			# When user is not in guild, member is None. 
			if member != None:
				nick = member.display_name
				name = member.name
				# Filter out Emojis in names
				for i in range(len(nick)):
					if nick[i] in UNICODE_EMOJI['en']:
						nick = "".join((nick[:i],"#",nick[i+1:]))
				for i in range(len(name)):
					if name[i] in UNICODE_EMOJI['en']:
						name = "".join((name[:i],"#",name[i+1:]))
			else:
				# When user is not in guild.
				nick = "Not on guild"
				name = f"ID: {userID}"
			# Get user data from userdata.json.
			hours = self.jh.getUserHours(userID)
			messages = self.jh.getUserTextCount(userID)
			xp = self.xpf.giveXP(self.jh.getUserVoice(userID), self.jh.getUserText(userID))
			level = self.jh.getUserLevel(userID)
			# formatting for leaderboard.
			leaderborad += f"```md\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(53-len(nick+name))}({name})    Hours: {' '*(6-len(str(hours)))}{hours}     Messages: {' '*(4-len(str(messages)))}{messages}     Experience: {' '*(6-len(str(xp)))}{xp}      Level: {' '*(3-len(str(level)))}{level}\n```\n"
			rank += 1
		return leaderborad

	@staticmethod
	def getMessageState(message):
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
			return (0,0)

		# Some features relay on the reactions to identify them. For example the leaderboard.	
		reactions = message.reactions
		reactionstr = ""
		textBeginn = message.content[:5]
		for reaction in reactions:
			reactionstr += str(reaction)
		state = 0

		# Check for leaderboard
		if reactionstr == "⏫⬅➡⏰💌":
			state = 1
		elif reactionstr == "⏫⬅➡💌🌟":
			state = 2
		elif reactionstr == "⏫⬅➡⏰🌟":
			state = 3

		# Check for poll via the start of the message string.
		elif textBeginn == "```md" and reactionstr[0:2] == "1⃣":
			return (4,0)

		# Check for data protection declaration. 
		elif textBeginn == "**Not":
			return (5,0)

		# Check for give roles message.
		elif textBeginn == "**Cho":
			return(6,0)

		# Normal message or not implemented yet.
		else:
			return (0,0)

		# Is leaderboard and now find the page of it.
		pageTopRank = int(str(message.content)[6:10])
		return (state, pageTopRank//10)

	async def sendServerModMessage(self, string, embed = None):
		"""
		param string:	String which is send.
		Sends all Mods on the guild string. 
		!!! Not modular and sends it to COO !!!
		"""
		server = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		for user in server.members:
			if self.hasRole(user.id, "COO"):
				await user.send(string, embed = embed)

	async def sendModsMessage(self, string, embed = None):
		"""
		param string:	String which will be sent.

		Sends all Mods of the Bot with privilege level of 1 or higher the string. 
		"""
		await self.sendMessageToPrivilage(string, 1, embed = embed)

	async def sendOwnerMessage(self, string, embed = None):
		"""
		param string:	String which is send.

		Sends all Owners of the Bot with privilege level of 2 or higher the string. 
		"""
		await self.sendMessageToPrivilage(string, 2, embed = embed)

	async def sendMessageToPrivilage(self, string, level, embed = None):
		"""
		param string:	String which is send.
		param level:	Integer of the minimum level. 

		Sends all Users of the Bot with privilege level of level or higher the string. 
		"""
		for x in self.jh.getInPrivilege():
			if self.jh.getPrivilegeLevel(x) >= level:
				user = self.bot.get_user(int(x))
				await user.send(string, delete_after=604800 ,embed = embed)

	async def log(self, message, level):
		"""
		param message:	String to write to log.txt.
		param level:	Sends to whom level is high enough.

		Saves a message to the log.txt and messages all Users with a privilege level of level or higher.
		"""
		message = str(datetime.datetime.now())+":\t" + message
		# Send message
		await self.sendMessageToPrivilage(message, level)
		# Log to log.
		Utils.logToFile(message)
		print(message)

	@staticmethod
	def logToFile(message, withDate = False):
		"""
		param message:	String to write to log.txt.

		Writes message to log.txt
		"""
		if withDate:
			message = str(datetime.datetime.now())+":\n" + message
		message = "\n" + message
		logfile = str(os.path.dirname(os.path.dirname(__file__))) + "/data/log.txt"
		with open(logfile,'a') as l:
			l.write(f"{message}\n")

	def getJH(self):
		"""
		Returns the Jsonhandel object in self.jh.
		"""
		return self.jh

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
