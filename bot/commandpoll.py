import discord
from discord.utils import get
from discord.ext import commands
from .decorators import *

def hasAnyRole(*items):
		"""
		commands.has_any_role() does not work in DM since a users can't have roles.
		This on pulls the roles from the configured guilde and makes the same check as commands.has_any_role().
		"""
		def decorator(func):
			def wrapper(*args, **kwargs):
				if Commandpoll.helpf.hasOneRole(args[1].author.id, [*items]):
					return func(*args, **kwargs)
				return passFunc()
			return wrapper
		return decorator

class Commandpoll(commands.Cog, name='Poll Commands'):
	"""These Commands are for creating polls."""

	helpf = None

	def __init__(self, bot, helpf, poll, jh):
		super(Commandpoll, self).__init__()
		self.bot = bot
		self.helpf = helpf
		self.poll = poll
		self.jh = jh
		Commandpoll.helpf = helpf

	@commands.command(name='poll')
	async def pollCommandInterpretor(self, ctx, *inputs):
		lenght = len(inputs)
		if lenght == 2 and inputs[0] == "close":
			await self.poll_close(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "create":
			await self.pollCreate(ctx, inputs[1])

		elif lenght == 1 and inputs[0] == "list":
			await self.pollsList(ctx)

		elif lenght == 2 and inputs[0] == "close":
			await self.poll_close(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "open":
			await self.poll_open(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "publish":
			await self.poll_publish(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "rm":
			await self.poll_remove(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "show":
			await self.pollSend(ctx, inputs[1])

		elif lenght == 4 and inputs[0] == "op" and inputs[1] == "add":
			await self.optionAdd(ctx, *inputs[2:4])

		elif lenght == 4 and inputs[0] == "op" and inputs[1] == "rm":
			await self.polloptionRemove(ctx, *inputs[2:4])

		else:
			await ctx.author.send(f"Command \"poll {' '.join(inputs)}\" is not valid.")

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def pollCreate(self, ctx, pollName):
		#Creates a poll with the given name.
		#Sends a overwiew of the poll.
		message = ""
		if len(pollName) <= 71:
			pollID = self.poll.newPoll(pollName)
			datum = self.poll.getDate(pollID)
			status = self.poll.getStatus(pollID)
			sumVotes = self.poll.getSumVotes(pollID)
			message = f"```md\n{pollID}\t{pollName}\t{datum}\t{status}\t{sumVotes}\n```\n"
			await self.helpf.log(f"User {ctx.author} created the poll {pollName} with ID: {pollID}.",1)
		else:
			message = "ERROR: The optionName is to long."
		await ctx.send(message)

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def pollSend(self, ctx, pollID):
		#Sends the poll with options to the user. 
		message = ""
		if self.poll.isAPollID(pollID):
			message = self.poll.pollString(pollID)
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def optionAdd(self, ctx, pollID, optionName):
		#Trys to add a option to the poll.
		message = ""
		if self.poll.isAPollID(pollID):
			if len(optionName) <=112:
				if not self.poll.optionAdd(pollID, str(optionName), 0):
					message = "ERROR: Option Name is already taken or poll is not CLOSED. Try another.\n"
				message += f"{self.poll.pollString(pollID)}"
			else:
				message = "ERROR: OptionName is to long."
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def polloptionRemove(self, ctx, pollID, optionName):
		#Trys to remove a option from a poll.
		message = ""
		if self.poll.isAPollID(pollID):
			if not self.poll.optionRemove(pollID, str(optionName)):
				message = "ERROR: Could not find option Name or poll is not CLOSED. Try another Name.\n"
			message += f"{self.poll.pollString(pollID)}"
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@isInChannelOrDM("🚮spam")
	@hasAnyRole("CEO","COO","chairman","associate")
	async def pollsList(self, ctx):
		#Sends a list of all polls the the channel.
		message = ""
		for pollID in self.poll.getAllPolls()[::-1]:
			message += self.poll.pollHeader(pollID)
		if message == "":
			message = "No active polls."
		await ctx.send(message)

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def poll_remove(self, ctx, pollID):
		#Removes a poll.
		message = ""
		if self.poll.isAPollID(pollID):
			pollName = self.poll.getName(pollID)
			if len(self.poll.getOptions(pollID)) == 0 or self.jh.getPrivilegeLevel(ctx.author.id) >= 1 or self.helpf.hasRole(ctx.author.id, "chairman"):
				if self.poll.removePoll(pollID):
					message = f"Removed Poll {pollName}."
					await self.helpf.log(f"User {ctx.author.mention} removed the poll: \"{pollName}\".", 2)
					channel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
					server = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
					await channel.send(f"User {ctx.author.mention} removed the poll: \"{pollName}\".")
				else:
					message = "ERROR: Something strange happend."
					await self.helpf.log(f"User {ctx.author.name} tried to remove poll: \"{pollName}\", {pollID} with message: {ctx.message.content}")
			else:
				message = "Can't remove a poll with options. Contacted Bot Mods to review your command. The poll will maybe be removed."
				await self.helpf.sendServerModMessage(f"User {ctx.author.mention} wants to removed the poll: \"{pollName}\". Use Command \"+poll_remove {pollID}.\" to remove to poll.")
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)


	@isNotInChannelOrDM("📂log","📢info","⏫level")
	@hasAnyRole("CEO","COO","chairman")
	async def poll_open(self, ctx, pollID):
		[messageID, channelID] = self.poll.getMessageID(pollID)
		self.poll.pollOpen(pollID)
		# Test if has a send poll string somewhere
		if messageID and channelID:
			# poll has been send somewhere => delete old one
			channel = self.bot.get_channel(int(channelID))
			messageToDelet = await channel.fetch_message(int(messageID))
			await messageToDelet.delete()
		# Poll is open => send it
		if self.poll.getStatus(pollID) == "OPEN":
			# Send poll
			text = self.poll.pollString(pollID)
			messageSend = await ctx.send(content=f"{text}{ctx.author.mention}")
			reactionsarr = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣","6⃣","7⃣"]
			for emoji in reactionsarr[:len(self.poll.getOptions(pollID))]:
				await messageSend.add_reaction(emoji)
			self.poll.setMessageID(pollID, messageSend.id, messageSend.channel.id)
			await self.helpf.log(f"User {ctx.author.mention} opened the poll {pollID} in channel {ctx.channel.name}.",1)
		elif self.poll.getStatus(pollID) == "CLOSED":
			message = f"ERROR: You can't open a poll with only 1 polloption"
			await ctx.author.send(message)
		await ctx.message.delete()

	@isDM()
	@hasAnyRole("CEO","COO","chairman")
	async def poll_close(self, ctx, pollID):
		[messageID, channelID] = self.poll.getMessageID(pollID)
		if self.poll.pollClose(pollID) and messageID and channelID:
			channel = self.bot.get_channel(int(channelID))
			message = await channel.fetch_message(int(messageID))
			if message != None:
				await message.clear_reactions()
				await message.edit(content=f"{self.poll.pollString(pollID)}")
				# self.poll.setMessageID(pollID, '', '')
				await self.helpf.log(f"User {ctx.author.name} cloesed poll: \"{self.poll.getName(pollID)}\"",1)
		else:
			await ctx.send("ERROR: Can't close Poll")	

	@isNotInChannelOrDM("📂log","📢info","⏫level")
	@hasAnyRole("CEO","COO","chairman")
	async def poll_publish(self, ctx, pollID):
		if self.poll.pollPublish(pollID):
			# Delet OPEN poll to resend as published
			[messageID, channelID] = self.poll.getMessageID(pollID)
			channel = self.bot.get_channel(int(channelID))
			message = await channel.fetch_message(int(messageID))
			await message.delete()
			# Send published poll
			text = self.poll.pollStringSortBy(pollID, 1)
			message = await ctx.send(content=text)
			self.poll.setMessageID(pollID, '', '')
			# Give voters XP
			for vote in self.poll.getVotes(pollID):
				self.jh.addReactionXP(vote[0], 25)
		else:
			await ctx.send(content="ERROR: Poll does not exist or poll is not OPEN.", delete_after=7200)
		await ctx.message.delete()			

def setup(bot, helpf, poll, jh):
	bot.add_cog(Commandpoll(bot, helpf, poll, jh))