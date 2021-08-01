import discord
from discord.utils import get, find
from discord.ext import commands
from .jsonhandel import Jsonhandel
from .xpfunk import Xpfunk
import math
import sys
import os
import datetime
import hashlib

from emoji import UNICODE_EMOJI

class Helpfunc(object):
	"""
	General functions
	"""
	def __init__(self, bot, jh, xpf):
		super(Helpfunc, self).__init__()
		self.bot = bot
		self.jh = jh
		self.xpf = xpf

	def getVoiceChannelsFrom(self, serverid):
		guilde = self.bot.get_guild(int(serverid))
		return guilde.voice_channels

	def getTextChannelsFrom(self, serverid):
		guilde = self.bot.get_guild(int(serverid))
		return guilde.text_channels

	def addMembersOnlineVoiceXp(self, serverid):
		""" 
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
			if len(membersInChannel) >= 2:
				membersNotMutedOrBot = [member for member in membersInChannel if not (member.voice.self_mute or member.bot)]
				self.jh.addAllUserVoice(membersNotMutedOrBot)
				membersStreamOrVideo = [member for member in membersNotMutedOrBot if (member.voice.self_video or member.voice.self_stream)]
				self.jh.addAllUserVoice(membersStreamOrVideo)

	async def updateRoles(self):
		# Gives members role in rolesList if they have the level in roleXPNeedList
		# Also memers needs to have "etwasse" or "rookie"
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		membersList = guilde.members
		for member in membersList:
			if self.jh.isInData(member.id):
				if self.hasOneRole(member.id, {"etwasse", "rookie"}):
					userLevel = self.jh.getUserLevel(member.id)
					rolesList = self.jh.getRoles()
					roleXPNeedList = self.jh.getRolesXPNeed()
					i = len([level for level in roleXPNeedList if int(level) <= userLevel])
					await self.giveRoles(member.id, rolesList[:i])

	def hasRole(self, userID, role):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		return role in [x.name for x in member.roles]

	def hasRoles(self, userID, roles):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		return set(roles).issubset({x.name for x in member.roles})

	def hasOneRole(self, userID, roles):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		return len(set(roles).intersection({x.name for x in member.roles})) >= 1

	async def giveRole(self, userID, roleName):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		role = get(guilde.roles, name=roleName)
		await member.add_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got role {roleName}.",1)

	async def giveRoles(self, userID, roleNames):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		rolesList = tuple(find(lambda role: str(role.id) == r or role.name == r, list(set(guilde.roles)-set(member.roles))) for r in roleNames)
		rolesList = [x for x in rolesList if x != None]
		memberRolesPrev = member.roles
		if len(rolesList) > 0:
			await member.add_roles(*rolesList)
			rolesAfter = {role.name for role in member.roles if not role in memberRolesPrev}
			await self.log(f"User {member.name} aka {member.nick} got roles {rolesAfter}.",1)

	async def removeRole(self, userID, roleName):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		role = get(guilde.roles, name=roleName)
		await member.remove_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got his role {roleName} removed.",1)

	async def removeRoles(self, userID, roleNames, reason = None):
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = guilde.get_member(int(userID))
		rolesList = tuple(find(lambda role: str(role.id) == r or role.name == r, list(set(guilde.roles)-set(member.roles))) for r in roleNames)
		rolesList = [x for x in rolesList if x != None]
		memberRolesPrev = member.roles
		if len(rolesList) > 0:
			await member.remove_roles(*rolesList, reason = reason)
			rolesAfter = {role.name for role in memberRolesPrev if not role in member.roles}
			await self.log(f"User {member.name} aka {member.nick} got his roles {str(rolesAfter)} removed.",1)

	async def levelAkk(self):
		# Updates the level of all users in data
		for userID in self.jh.getUserIDsInData():
			voice = self.jh.getUserVoice(userID)
			text = self.jh.getUserText(userID)
			oldLevel = self.jh.getUserLevel(userID)
			levelByXP = self.xpf.levelFunk(voice, text)
			if levelByXP != oldLevel:
				self.jh.updateLevel(userID, levelByXP)
				# Write new level to channel
				levelchannel = self.bot.get_channel(int(self.jh.getFromConfig("levelchannel")))
				member = self.bot.get_user(int(userID))
				await levelchannel.send(f"**{member.mention}** reached level **{levelByXP}**.")

	def getLeaderboardPageBy(self, page, sortBy):
		"""
		sortBy:
			0 => Sort by voice + text
			1 => Sort by voice
			2 => Sort by textcount
		page: which page of the leaderboard is showen. A page contains 10 entrys
		"""
		userIDs = self.jh.getSortedDataEntrys(page*10, (page+1)*10 ,sortBy)[::-1]
		leaderborad = ""
		rank = page*10+1
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		# Generate Leaderboard String
		for userID in userIDs:
			member = guilde.get_member(int(userID))
			if member != None:
				nick = member.display_name
				name = member.name
				# Filter out Emojis in names
				for i in range(len(nick)):
					if nick[i] in UNICODE_EMOJI['en']:
						nick = "".nick((re[:i],"#",nick[i+1:]))
				for i in range(len(name)):
					if name[i] in UNICODE_EMOJI['en']:
						name = "".name((re[:i],"#",name[i+1:]))
			else:
				nick = "Not on guilde"
				mane = f"ID: {userID}"
			hours = self.jh.getUserHours(userID)
			messages = self.jh.getUserTextCount(userID)
			xp = self.xpf.giveXP(self.jh.getUserVoice(userID), self.jh.getUserText(userID))
			level = self.jh.getUserLevel(userID)
			leaderborad += f"```md\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(53-len(nick+name))}({name})    Hours: {' '*(6-len(str(hours)))}{hours}     Messages: {' '*(4-len(str(messages)))}{messages}     Experience: {' '*(6-len(str(xp)))}{xp}      Level: {' '*(3-len(str(level)))}{level}\n```\n"
			rank += 1
		return leaderborad

	async def getMessageFromPayload(self, payload):
		channel = self.bot.get_channel(int(payload.channel_id))
		message = await channel.fetch_message(int(payload.message_id))
		return message

	def getMessageState(self, message):
		"""
		State (0,0): Normal Message
		State (1,x): Leaderboard sorted by XP on page x
		State (2,x): Leaderboard sorted by Voice on page x
		State (3,x): Leaderboard sorted by TextCount on page x
		State (4,0): Poll
		State (5,0): data protection declaration
		State (6,0): giveRoles message

		Analyzes message to which bot function it belongs
		"""
		if not message.author.bot:
			return (0,0)
		reactions = message.reactions
		reactionstr = ""
		textBeginn = message.content[:5]
		for reaction in reactions:
			reactionstr += str(reaction)
		state = 0
		if reactionstr == "⏫⬅➡⏰💌":
			state = 1
		elif reactionstr == "⏫⬅➡💌🌟":
			state = 2
		elif reactionstr == "⏫⬅➡⏰🌟":
			state = 3
		elif textBeginn == "```md" and reactionstr[0:2] == "1⃣":
			return (4,0)
		elif textBeginn == "**Not":
			return (5,0)
		elif textBeginn == "**Cho":
			return(6,0)
		else:
			return (0,0)
		pageTopRank = int(str(message.content)[6:10])
		return (state, pageTopRank//10)

	def getLeaderboardChange(self, message):
		"""
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
		reactions = message.reactions
		i = 0
		while reactions[i].count == 1:
			i += 1
		return i

	async def sendServerModMessage(self, string):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		for user in server.members:
			if self.hasRole(user.id, "COO"):
				await user.send(string)

	async def sendModsMessage(self, string):
		await self.sendMessageToPrivilage(string, 1)

	async def sendOwnerMessage(self, string):
		await self.sendMessageToPrivilage(string, 2)

	async def sendMessageToPrivilage(self, string, level):
		for x in self.jh.getInPrivilege():
			if int(self.jh.getPrivilegeLevel(x)) >= level:
				owner = self.bot.get_user(int(x))
				await owner.send(string, delete_after=604800)

	async def log(self, message, level):
		message = str(datetime.datetime.now())+":\t"+message
		await self.sendMessageToPrivilage(message, level)
		logfile = str(os.path.dirname(os.path.abspath(__file__)))[:-4]+"/bin/log.txt"
		with open(logfile,'a') as l:
			l.write(f"{message}\n")
		print(message)

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
