import asyncio
import time
import os
import json
import traceback

from discord.ext import tasks, commands

from datahandler.jsonhandel import Jsonhandel
from datahandler.sub import Sub
from helpfunctions.utils import Utils
from helpfunctions.decorators import isBotOwnerCommand
from helpfunctions.xpfunk import Xpfunk


class Subroutine(commands.Cog):
	"""
	Manages subroutines of bot.
	Bot subroutines are functions, which are called after some time has passed.
	These features are not event driven like all others.

	Also handles all changes which will be made to sub.json.

	Subroutines:
		Removes role
		Give role once
		(Not yet moved from commandowner.startlog) Log users in channel and gives XP
	"""

	def __init__(self, bot):
		super(Subroutine, self).__init__()
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		self.sub = Sub()
		self.xpf = Xpfunk()
		self.subRoutine.start()

	@commands.command(name = "issubrun")
	@isBotOwnerCommand()
	async def isSubroutineRunning(self, ctx):
		await ctx.send(self.subRoutine.is_running())

	def startSubRoutine(self):
		"""
		Creates a new asyncio event loop in which the subroutine runs.
		If the subroutine is already running, nothing happens.
		"""
		if self.subRoutine.is_running():
			# Subroutine is running
			return

		self.subRoutine.start()

	async def stopSubRoutine(self):
		if not self.subRoutine.is_running():
			# Subroutine is not running
			return
		await self.utils.log("[Subroutine] Stopping subRoutine",2)
		self.subRoutine.stop()

	@tasks.loop(seconds = 120)
	async def subRoutine(self):
		"""
		Runs the subroutine. After a determent waiting time, the features will be called.

		Features implemented (will be carried out in this order):
			Remove role
			Give role once
		"""
		self.sub.reloadSubjson()
		"""
		bufferTime says how long an offset can be used when hitting an interval.
		!!! Should not be greater than seconds in @taks.loop !!!
		"""
		bufferTime = 120

		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		currentTime = time.time()
		
		"""
		Remove role subroutine:
			Continuously removes the role in a given interval starting on the offset.
		"""
		await self.removeRoleSubroutineFunction(currentTime, bufferTime, guild)

		"""
		Give role once:
			Gives a member a role when the time window is hit.
			The time window is defined with an offset and interval.
			If the interval hit beginning on the offset, the role is given once. 
		"""
		await self.giveRoleOnceSubroutineFunction(currentTime)

		"""
		GiveOnlineUserXP:
			Gives user depending on the rules of addMembersOnlineVoiceXp voice XP.
		"""
		await self.giveOnlineUserXPSubroutineFunction(guild.id)

	@subRoutine.before_loop
	async def beforSubroutineStart(self):
		"""
		Waits before starting the loop for the bot to be ready.
		"""
		await self.bot.wait_until_ready()

	async def removeRoleSubroutineFunction(self, currentTime, bufferTime, guild):
		"""
		param currentTime:	Float time on what the timing will be compared on.

		Removes the role for all users in the guild.
		First scans sub.json for 'removeRole' events. 
		Determines if they should be carried out and carries them out.
		"""
		for toRemove in self.sub.getRoleRemoveIDs():
			if not toRemove.isdigit():
				await self.utils.log(f"[Subroutine ERROR] In 'removeRoleSubroutineFunction'. Key {toRemove} in removeRole is no role ID. Remove key to resolve this error.",2)
				continue
			offset, interval = self.sub.getContantOfRoleRemoveID(toRemove)
			if not offset and not interval:
				await self.utils.log(f"[Subroutine ERROR] In 'removeRoleSubroutineFunction'. Invalid offset: {offset} or interval: {interval}.",2)
			if (currentTime - offset) % interval < bufferTime and currentTime > offset:
				role = guild.get_role(int(toRemove))
				if role == None:
					await self.utils.log(f"[Subroutine ERROR] In 'removeRoleSubroutineFunction'. Role with ID {toRemove} is not in guild. Remove it from 'sub.json' to fix this issue.",2)
				else:
					# Remove roles
					for member in role.members:
						await self.utils.removeRoles(member.id, [toRemove])

	async def giveRoleOnceSubroutineFunction(self, currentTime):
		"""
		param currentTime:	Float time on what the timing will be compared on.

		Gives member a role if conditions are right.
		Scans sub.json for timing, userID and roleID.
		Determines if they should be carried out and carries them out.
		"""
		entrysToDelet = []
		for toGiveOnce in self.sub.getGiveRoleOnceIDs():
			time, userID, roleID = self.sub.getContantOfGiveRoleOnceID(toGiveOnce)
			if time <= currentTime:
				# Gives role to member and clears entry in sub.json.
				try:
					await self.utils.giveRoles(userID, [roleID])
				except AttributeError as e:
					# When user is not anymore in the guild.
					await self.utils.log("[ERROR] Tried to give member role which is not in the guild.",2)
					await self.utils.log(traceback.format_exc(),2)
				entrysToDelet.append(toGiveOnce)
		self.sub.deleteGiveRoleOnce(entrysToDelet)

	async def giveOnlineUserXPSubroutineFunction(self, guild):
		"""
		param guild:	ID of guild one which users will be given XP

		Gives user depending on the rules of addMembersOnlineVoiceXp voice XP.
		"""
		if self.jh.getFromConfig("log") == "False":
			return 
		self.addMembersOnlineVoiceXp(guild)
		await self.levelAkk()
		await self.updateRoles()
		self.jh.saveData()

	async def updateRoles(self):
		"""
		Gives members role in rolesList if they have the level in roleXPNeedList.
		Also, members needs to have "✅". Another subserver (not yet implemented) are also ok.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		membersList = guild.members
		for member in membersList:
			if self.jh.isInData(member.id):
				if self.utils.hasOneRole(member.id, {"✅"}):
					# Give all roles user is qualified for even if he already has some roles.
					userLevel = self.jh.getUserLevel(member.id)
					rolesList = self.jh.getRoles()
					roleXPNeedList = self.jh.getRolesXPNeed()
					i = len([level for level in roleXPNeedList if int(level) <= userLevel])
					await self.utils.giveRoles(member.id, rolesList[:i])

	def addMembersOnlineVoiceXp(self, serverid):
		""" 
		param serverid:	guild ID of a Discord guild.

		Increments to voice XP of member in voice channel if
			1)	member is not alone in channel
			2)	member is not a bot
		Gain extra XP if
			1)	member has cam on
			2)	member is streaming
		"""
		guild = self.bot.get_guild(int(serverid))
		voiceChanels = [channel for channel in guild.voice_channels if not self.jh.isInBlacklist(channel.id)]
		# Total all connected members
		for channel in voiceChanels:
			membersInChannel = [member for member in channel.members if not member.bot]
			# Check if more than one person is in channel
			if len(membersInChannel) >= 2:
				membersNotMutedOrBot = [member for member in membersInChannel if not (member.voice.self_mute or member.bot)]
				self.jh.addAllUserVoice([member.id for member in membersNotMutedOrBot])
				# Extra XP
				membersStreamOrVideo = [member for member in membersNotMutedOrBot if (member.voice.self_video or member.voice.self_stream)]
				self.jh.addAllUserText([member.id for member in membersStreamOrVideo])

	async def levelAkk(self):
		"""
		Updates the level of all users in data
		"""
		for userID in self.jh.getUserIDsInData():
			voice = self.jh.getUserVoice(userID)
			text = self.jh.getUserText(userID)
			oldLevel = self.jh.getUserLevel(userID)
			levelByXP = self.xpf.levelFunk(voice, text)
			# Check for level change
			if levelByXP != oldLevel:
				self.jh.updateLevel(userID, levelByXP)
				# Write new level to channel
				levelchannel = self.bot.get_channel(int(self.jh.getFromConfig("levelchannel")))
				user = self.bot.get_user(int(userID))
				userMention = "Unknown user"
				if user != None:
					userMention = user.mention
				await levelchannel.send(f"**{userMention}** reached level **{levelByXP}**.")

def setup(bot):
	bot.add_cog(Subroutine(bot))
