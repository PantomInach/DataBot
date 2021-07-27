import discord
from discord.utils import get
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
	"""docstring for """
	def __init__(self, bot, jh, xpf):
		super(Helpfunc, self).__init__()
		self.bot = bot
		self.jh = jh
		self.xpf = xpf

	"""
	TODO: Simplify/Make it better
	CODE: (Beginns at voiceChanels = server.channels)
		channels = []
		for x in voiceChannels:
			if x.type == "voice":
				channels.append(x.id)
		return channels
				
	"""
	async def channelList(self, serverid):
		server = self.bot.get_guild(int(serverid))
		voiceChanels = server.channels
		length = {"T":16, "V":17, "C":20}
		arr = str(voiceChanels)[1:].split('>, ')
		channels = []
		for x in arr:
			idAt = length[str(x)[1]]
			channels.append(str(x)[idAt:idAt+18])
		return channels

	"""
	TODO: Simplify/Make it better
	CODE: (Beginns at voiceChanels = server.channels)
		channels = []
		for x in textChannels:
			if x.type == "text":
				channels.append(x.id)
		return channels
				
	"""
	async def textList(self, serverid):
		server = self.bot.get_guild(int(serverid))
		channels = server.channels
		length = {"T":16, "V":17, "C":20}
		arr = str(channels)[1:].split('>, ')
		textChannels = []
		for x in arr:
			idAt = length[str(x)[1]]
			textChannels.append(str(x)[idAt:idAt+18])
		return textChannels

	async def connectedUserFrom(self, serverid):
		server = self.bot.get_guild(int(serverid))
		voiceChanels = server.channels
		#TODO: remove this string manipulation for something in the api
		arr = str(voiceChanels)[1:].split('>, ')
		channelids = []
		for i in arr:
			if str(i)[1:6] == "Voice":
				channelids.append(i[17:35])
		#Filters out 
		blacklist = self.jh.config["serverVoiceBlacklist"]
		channelids = set(channelids)-set(blacklist)
		#Get users connected to voice channels
		memids = []
		for channelid in channelids:
			channel = self.bot.get_channel(int(channelid))
			members = channel.members
			if len([x for x in members if not x.bot]) <= 1:
				members = []
			for member in members:
				if not (member.voice.self_mute or member.bot):
					memids.append(member.id)
					if member.voice.self_video or member.voice.self_stream:
						self.jh.addNewDataEntry(member.id)
						self.jh.data[str(member.id)]["Text"] = str(int(self.jh.data[str(member.id)]["Text"])+1)
		return memids

	#TODO: Create new Class Roles, to handel roles spezific commands? 
	async def updateRoles(self):
		print("Starting to update roles...")
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		#TODO: remove this string manipulation for something in the api
		membersList = str(server.members)[1:].split('>, ')
		memids = []
		for members in membersList:
			memids.append(members[11:29])
		for members in memids:
			if self.jh.isInData(members):
				userLevel = int(self.jh.data[members]["Level"])
				rolesList = self.jh.getRoles()
				roleXPNeedList = self.jh.getRolesXPNeed()
				for i in range(len(rolesList)):
					if userLevel >= int(roleXPNeedList[i]) and not await self.hasRole(members, rolesList[i]) and (await self.hasRole(members, "rookie") or await self.hasRole(members, "etwasse")):
						memberclass = self.bot.get_user(int(members))
						await self.giveRole(members, rolesList[i])
		print("Updated Roles.")

	async def hasRole(self, userID, roleString):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = server.get_member(int(userID))
		return roleString in [x.name for x in member.roles]

	async def giveRole(self, userID, roleName):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = server.get_member(int(userID))
		role = get(server.roles, name=roleName)
		await member.add_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got role {roleName}.",1)

	async def removeRole(self, userID, roleName):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = server.get_member(int(userID))
		role = get(server.roles, name=roleName)
		await member.remove_roles(role)
		await self.log(f"User {member.name} aka {member.nick} got his role {roleName} removed.",1)

	async def removeRoles(self, userID, roleNames):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		member = server.get_member(int(userID))
		roles = []
		for roleName in roleNames:
			if await self.hasRole(userID, roleName):
				await member.remove_roles(get(server.roles, name=roleName))
		await self.log(f"User {member.name} aka {member.nick} got his roles {str(roleNames)} removed.",1)

	async def levelAkk(self):
		for userID in self.jh.data:
			voice = self.jh.data[userID]["Voice"]
			text = self.jh.data[userID]["Text"]
			temp = self.jh.data[userID]["Level"]
			self.jh.data[userID]["Level"] = self.xpf.levelFunk(voice, text)
			if temp != self.jh.data[userID]["Level"]:
				levelchannel = self.bot.get_channel(int(self.jh.getFromConfig("levelchannel")))
				level = self.jh.data[userID]["Level"]
				member = self.bot.get_user(int(userID))
				await levelchannel.send(f"**{member.mention}** reached level **{level}**.")
		print("\tUpdated levels.")

	"""
	sort 1: Sort by xp (voice+text)
	sort 2: Sort by voice
	sort 3: Sort by textcount
	"""
	async def sortMyDataBy(self, users, data, sort):
		reuser = []
		redata = []
		sm = [[1,1,0],[0,1,0],[0,0,1]]
		reuser.append(users[0])
		redata.append(data[0])
		j = 1
		for entry in data[1:]:
			xpentry = int(entry["Text"])*sm[sort][0] + int(entry["Voice"])*sm[sort][1] + int(entry["TextCount"])*sm[sort][2]
			i = 0
			while i<len(reuser) and xpentry < int(redata[i]["Text"])*sm[sort][0]+int(redata[i]["Voice"])*sm[sort][1] + int(redata[i]["TextCount"])*sm[sort][2]:
				i += 1
			redata.insert(i,entry)
			reuser.insert(i,users[j])
			j += 1
		re = []
		re.append(reuser)
		re.append(redata)
		return re

	#page x beginns at 0 with ranks 1-10
	async def getLeaderboardXBy(self, x, sort):
		users = [y for y in self.jh.data]
		data = [self.jh.data[y] for y in users]
		temp = await self.sortMyDataBy(users, data, sort-1)
		users = temp[0]
		data = temp[1]
		re = ""
		start = x*10
		end = (x+1)*10 if (x+1)*10 <= len(users) else len(users)
		for i in range(start,end):
			rank = i+1
			server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
			member = server.get_member(int(users[i]))
			if member != None:
				nick = member.display_name
				name = member.name
			else:
				user = self.bot.get_user(int(users[i]))
				nick = "Not on server"
				name = f"ID: {users[i]}"
			hours = round(int(data[rank-1]["Voice"])/30.0, 1)
			messages = data[rank-1]["TextCount"]
			xp = int(data[rank-1]["Voice"])+int(data[rank-1]["Text"])	
			level = data[rank-1]["Level"]
			re += f"```md\n{' '*(4-len(str(rank)))}{rank}. {nick}{' '*(53-len(nick+name))}({name})    Hours: {' '*(6-len(str(hours)))}{hours}     Messages: {' '*(4-len(str(messages)))}{messages}     Experience: {' '*(6-len(str(xp)))}{xp}      Level: {' '*(3-len(str(level)))}{level}\n```\n"
			for i in range(len(re)):
				if re[i] in UNICODE_EMOJI['en']:
					re = "".join((re[:i],"#",re[i+1:]))
				if re[i] == "_" or re[i] == "*":
					re = "".join((re[:i]," ",re[i+1:]))
		return re

	async def getMessageFromPayload(self, payload):
		channel = self.bot.get_channel(int(payload.channel_id))
		message = await channel.fetch_message(int(payload.message_id))
		return message

	"""
	State (0,0): Normal Message
	State (1,x): Leaderboard sorted by XP on page x
	State (2,x): Leaderboard sorted by Voice on page x
	State (3,x): Leaderboard sorted by TextCount on page x
	State (4,0): Poll
	State (5,0): data protection declaration
	State (6,0): giveRoles message
	"""
	async def getMessageState(self, message):
		if not message.author.bot:
			return (0,0)
		reactions = message.reactions
		reactionstr = ""
		text = message.content[:5]
		for reaction in reactions:
			reactionstr += str(reaction)
		state1 = 0
		if reactionstr == "⏫⬅➡⏰💌":
			state1 = 1
		elif reactionstr == "⏫⬅➡💌🌟":
			state1 = 2
		elif reactionstr == "⏫⬅➡⏰🌟":
			state1 = 3
		elif text == "```md" and reactionstr[0:2] == "1⃣":
			return (4,0)
		elif text == "**Not":
			return (5,0)
		elif text == "**Cho":
			return(6,0)
		else:
			return (0,0)
		pagetoprank = int(str(message.content)[6:10])
		return (state1, math.floor(pagetoprank/10))

	"""
	0: to first page
	1: page befor
	2: page after
	3: sort xp
	4: sort voice
	5: sort textcount
	"""
	async def messageToState(self, message):
		reactions = message.reactions
		i = 0
		while reactions[i].count == 1:
			i += 1
		if i<3:
			return i
		if str(reactions[i]) == "⏰":
			return 4
		if str(reactions[i]) == "💌":
			return 5
		if str(reactions[i]) == "🌟":
			return 3
		return 6

	async def voteOption(self, message):
		reactions = message.reactions
		i = 0
		while reactions[i].count == 1:
			i += 1
		return i

	async def sendServerModMessage(self, string):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		for user in server.members:
			if await self.hasRole(user.id, "COO"):
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


