import discord
from discord.utils import get, find
from discord.ext import commands
import sys
import os
import datetime
import hashlib

from emoji import UNICODE_EMOJI

class Helpfunc(object):
	"""
	This Class holds multip purpose commands for all classes.
	"""
	def __init__(self, bot, jh, xpf):
		super(Helpfunc, self).__init__()
		self.bot = bot
		self.jh = jh
		self.xpf = xpf

	def getVoiceChannelsFrom(self, serverid):
		"""
		param serverid:	Guilde ID of a Discord Guilde.

		Gets the voice channels from a Discord Guilde.
		"""
		guilde = self.bot.get_guild(int(serverid))
		return guilde.voice_channels

	def getTextChannelsFrom(self, serverid):
		"""
		param serverid:	Guilde ID of a Discord Guilde.

		Gets the text channels from a Discord Guilde.
		"""
		guilde = self.bot.get_guild(int(serverid))
		return guilde.text_channels

	def addMembersOnlineVoiceXp(self, serverid):
		""" 
		param serverid:	Guilde ID of a Discord Guilde.

		Increments to voice xp of member in voice channel if
			1)	member is not alone in channel
			2)	member is not a bot
		Gain extra xp if
			1)	member has cam on
			2)	member is streaming
		"""
		guilde = self.bot.get_guild(int(serverid))
		voiceChanels = self.getVoiceChannelsFrom(serverid)
		# Filter out BlackList
		voiceChanels = [channel for channel in voiceChanels if not self.jh.isInBlacklist(channel.id)]
		# Total all connected members
		for channel in voiceChanels:
			membersInChannel = [member for member in channel.members if not member.bot]
			# Check if more than one person is in channel
			if len(membersInChannel) >= 2:
				membersNotMutedOrBot = [member for member in membersInChannel if not (member.voice.self_mute or member.bot)]
				self.jh.addAllUserVoice([member.id for member in membersNotMutedOrBot])
				# Extra XP
				membersStreamOrVideo = [member for member in membersNotMutedOrBot if (member.voice.self_video or member.voice.self_stream)]
				self.jh.addAllUserVoice([member.id for member in membersStreamOrVideo])

	async def updateRoles(self):
		"""
		Gives members role in rolesList if they have the level in roleXPNeedList.
		Also members needs to have "etwasse" or "rookie". Another SubServer (not yet implemented) are also ok.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		membersList = guilde.members
		for member in membersList:
			if self.jh.isInData(member.id):
				if self.hasOneRole(member.id, {"etwasse", "rookie"}):
					# Give all roles user is qualified for even if he already has some roles.
					userLevel = self.jh.getUserLevel(member.id)
					rolesList = self.jh.getRoles()
					roleXPNeedList = self.jh.getRolesXPNeed()
					i = len([level for level in roleXPNeedList if int(level) <= userLevel])
					await self.giveRoles(member.id, rolesList[:i])

	def hasRole(self, userID, role):
		"""
		param userID:	Is the userID from discord user as a String or int
		param role:		Which role to check. Needs to be the role's name.

		Checks if a member has the role.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		return role in [x.name for x in member.roles]

	def hasRoles(self, userID, roles):
		"""
		param userID:	Is the userID from discord user as a String or int
		param role:		List of roles which to check for. Needs to be the role's name.

		Checks if a member has all roles in roles.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		return set(roles).issubset({x.name for x in member.roles})

	def hasOneRole(self, userID, roles):
		"""
		param userID:	Is the userID from discord user as a String or int
		param roles:	List of roles which to check for. Needs to be the role's name.

		Checks if a member has any one role of roles.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		return len({x for x in member.roles if x.id in roles or x.name in roles}) >= 1

	async def giveRole(self, userID, roleName):
		"""
		param userID:	Is the userID from discord user as a String or int
		param roleName:	Role to give. Needs to be the role's name.

		Gives the member with userID the role roleName.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		role = get(guilde.roles, name=roleName)
		await member.add_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got role {roleName}.",1)

	async def giveRoles(self, userID, roleNames):
		"""
		param userID:	Is the userID from discord user as a String or int
		param roleNames:	List of roles to give. Needs to be the role's name or id.

		Gives the member with userID the roles roleNames.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		# Gets the roles to give by the role's name.
		rolesList = tuple(find(lambda role: str(role.id) == r or role.name == r, list(set(guilde.roles)-set(member.roles))) for r in roleNames)
		# Discord None roles, which resulte in errors.
		rolesList = [x for x in rolesList if x != None]
		memberRolesPrev = member.roles
		if len(rolesList) > 0:
			# Give roles
			await member.add_roles(*rolesList)
			# Get newly given roles for message.
			rolesAfter = {role.name for role in member.roles if not role in memberRolesPrev}
			await self.log(f"User {member.name} aka {member.nick} got roles {rolesAfter}.",1)

	async def removeRole(self, userID, roleName):
		"""
		param userID:	Is the userID from discord user as a String or int
		param roleName:	Role to remove. Needs to be the role's name.

		Removes the member with userID the role roleName.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		role = get(guilde.roles, name=roleName)
		await member.remove_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got his role {roleName} removed.",1)

	async def removeRoles(self, userID, roleNames, reason = None):
		"""
		param userID:	Is the userID from discord user as a String or int
		param roleNames:	List of roles to remove. Needs to be the role's name or id.
		param reason:	Specify reason in AuditLog from Guilde. Default is None.

		Removes the member with userID the roles roleNames.
		"""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = guilde.get_member(int(userID))
		# Gets the roles to remove by the role's name.
		rolesList = tuple(find(lambda role: str(role.id) == r or role.name == r, list(set(guilde.roles)-set(member.roles))) for r in roleNames)
		# Discord None roles, which resulte in errors.
		rolesList = [x for x in rolesList if x != None]
		memberRolesPrev = member.roles
		if len(rolesList) > 0:
			await member.remove_roles(*rolesList, reason = reason)
			# Get newly removed roles for message.
			rolesAfter = {role.name for role in memberRolesPrev if not role in member.roles}
			await self.log(f"User {member.name} aka {member.nick} got his roles {str(rolesAfter)} removed.",1)

	async def levelAkk(self):
		"""
		Updates the level of all users in data
		"""
		for userID in self.jh.getUserIDsInData():
			voice = self.jh.getUserVoice(userID)
			text = self.jh.getUserText(userID)
			oldLevel = self.jh.getUserLevel(userID)
			levelByXP = self.xpf.levelFunk(voice, text)
			# Check for level cahnge
			if levelByXP != oldLevel:
				self.jh.updateLevel(userID, levelByXP)
				# Write new level to channel
				levelchannel = self.bot.get_channel(int(self.jh.getFromConfig("levelchannel")))
				member = self.bot.get_user(int(userID))
				await levelchannel.send(f"**{member.mention}** reached level **{levelByXP}**.")

	def getLeaderboardPageBy(self, page, sortBy):
		"""
		param page:	Which page of the leaderboard is showen. Beginns with page 0. A page contains 10 entrys by default.
		param sortBy:
				0 => Sort by voice + text
				1 => Sort by voice
				2 => Sort by textcount
		
		Buildes a String for the Leaderboard on a given page with the rigth sorting.
		"""
		userIDs = self.jh.getSortedDataEntrys(page*10, (page+1)*10 ,sortBy)
		leaderborad = ""
		rank = page*10+1
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		# Generate Leaderboard String
		for userID in userIDs:
			member = guilde.get_member(int(userID))
			# When user is not in guilde, then member is None. 
			if member != None:
				nick = member.display_name
				name = member.name
				# Filter out Emojis in names
				for i in range(len(nick)):
					if nick[i] in UNICODE_EMOJI['en']:
						nick = "".join((leaderborad[:i],"#",nick[i+1:]))
				for i in range(len(name)):
					if name[i] in UNICODE_EMOJI['en']:
						name = "".join((leaderborad[:i],"#",name[i+1:]))
			else:
				# When user is not in guilde.
				nick = "Not on guilde"
				name = f"ID: {userID}"
			# Get user data from data.json.
			hours = self.jh.getUserHours(userID)
			messages = self.jh.getUserTextCount(userID)
			xp = self.xpf.giveXP(self.jh.getUserVoice(userID), self.jh.getUserText(userID))
			level = self.jh.getUserLevel(userID)
			# formating for leaderboard.
			leaderborad += f"```md\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(53-len(nick+name))}({name})    Hours: {' '*(6-len(str(hours)))}{hours}     Messages: {' '*(4-len(str(messages)))}{messages}     Experience: {' '*(6-len(str(xp)))}{xp}      Level: {' '*(3-len(str(level)))}{level}\n```\n"
			rank += 1
		return leaderborad

	async def getMessageFromPayload(self, payload):
		"""
		param payload:	Discord payload object.

		Gets the message String from the payload since it only contains channelID and messageID.
		"""
		channel = self.bot.get_channel(int(payload.channel_id))
		message = await channel.fetch_message(int(payload.message_id))
		return message

	def getMessageState(self, message):
		"""
		param message:	String of a message in Discord.

		Determaints in which state the message is. Used to identify Bot features such as Leaderbord or Polls.

		State (0,0): Normal Message
		State (1,x): Leaderboard sorted by XP on page x
		State (2,x): Leaderboard sorted by Voice on page x
		State (3,x): Leaderboard sorted by TextCount on page x
		State (4,0): Poll
		State (5,0): data protection declaration
		State (6,0): giveRoles message
		"""
		if not message.author.bot:
			return (0,0)

		# Some features relly on the reactions to identify them. For example the leaderboard.	
		reactions = message.reactions
		reactionstr = ""
		textBeginn = message.content[:5]
		for reaction in reactions:
			reactionstr += str(reaction)
		state = 0
		# Check for Leaderboard
		if reactionstr == "⏫⬅➡⏰💌":
			state = 1
		elif reactionstr == "⏫⬅➡💌🌟":
			state = 2
		elif reactionstr == "⏫⬅➡⏰🌟":
			state = 3

		# Check for poll via the start of the message String.
		elif textBeginn == "```md" and reactionstr[0:2] == "1⃣":
			return (4,0)

		# Check for data protection declaration. 
		elif textBeginn == "**Not":
			return (5,0)

		# Check for give roles message.
		elif textBeginn == "**Cho":
			return(6,0)

		# Normal message or not implemented jet.
		else:
			return (0,0)

		# Is Leaderbord and now ffind the page of it.
		pageTopRank = int(str(message.content)[6:10])
		return (state, pageTopRank//10)

	def getLeaderboardChange(self, message):
		"""
		param message:	Discord Message object. Should be from a Leaderboard.

		Gets how to change the leaderboard depending on its reactions.

		Return:
			0: to first page
			1: page befor
			2: page after
			3: sort xp
			4: sort voice
			5: sort textcount
		"""
		reactions = message.reactions
		i = 0
		while reactions[i].count == 1:
			i += 1
		if str(reactions[i]) == "🌟":
			i = 3
		elif str(reactions[i]) == "⏰":
			i = 4
		elif str(reactions[i]) == "💌":
			i = 5
		elif i > 5:
			i = 6
		return i

	def votedOption(self, message):
		"""
		param message:	Discord Message object. Should be from a Poll.

		Gets which option is voted for in a Poll created by the Bot via the reactions.
		"""
		reactions = message.reactions
		i = 0
		while reactions[i].count == 1:
			i += 1
		return i

	async def sendServerModMessage(self, string):
		"""
		param string:	String which is send.

		Sends all Mods on the Server string. 
		!!! Not mudular and sents it to COO !!!
		"""
		server = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		for user in server.members:
			if self.hasRole(user.id, "COO"):
				await user.send(string)

	async def sendModsMessage(self, string):
		"""
		param string:	String which is send.

		Sends all Mods of the Bot with privilage level of 1 or higher the string. 
		"""
		await self.sendMessageToPrivilage(string, 1)

	async def sendOwnerMessage(self, string):
		"""
		param string:	String which is send.

		Sends all Owners of the Bot with privilage level of 2 or higher the string. 
		"""
		await self.sendMessageToPrivilage(string, 2)

	async def sendMessageToPrivilage(self, string, level):
		"""
		param string:	String which is send.
		param level:	Integer of the minimum level. 

		Sends all Users of the Bot with privilage level of level or higher the string. 
		"""
		for x in self.jh.getInPrivilege():
			if self.jh.getPrivilegeLevel(x) >= level:
				owner = self.bot.get_user(int(x))
				await owner.send(string, delete_after=604800)

	async def log(self, message, level):
		"""
		param message:	String to write to log.txt.
		param level:	Sends to whomst level is high enough.

		Saves a message to the log.txt and messages all Users with a privilage level of level or higher.
		"""
		message = str(datetime.datetime.now())+":\t"+message
		# Send message
		await self.sendMessageToPrivilage(message, level)
		# Log to log.
		logfile = str(os.path.dirname(os.path.abspath(__file__)))[:-4]+"/bin/log.txt"
		with open(logfile,'a') as l:
			l.write(f"{message}\n")
		print(message)

	def getGuild(self guildid = None):
		"""
		param guildid:	integer of a guild ID. Default None.

		Returns the guilde with guildid.
		If guildid is not specified or False, than the guild from the conffig will be returned.
		"""
		if not guildid:
			guildid = int(jh.getFromConfig("guilde"))
		return bot.get_guild(guildid)

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