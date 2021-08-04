import discord
from discord.utils import get
from discord.ext import commands
from .decorators import *

def hasAnyRole(*items):
		"""
		commands.has_any_role() does not work in DM since a users can't have roles.
		This on pulls the roles from the conffigured guilde and makes the same check as commands.has_any_role().
		"""
		def predicate(ctx):
			return Commandpoll.helpf.hasOneRole(ctx.author.id, [role for role in items])
		return commands.check(predicate)

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

	@commands.command(name='poll_create', brief='Creates a new poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private messages.\nThis command creates a new poll with given name. The pollID is the lowest possible number available.\nAs an input you have to specify a name. If you want a name with spaces than set the name in \"\". The name can not be longer than 71 characters.')
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

	@commands.command(name='poll', brief='Prints a poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private messages.\nThis command shows the poll with the given ID with all its options.\nAs an input you need the poll ID, which you can get with \"+polls\".')
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

	@commands.command(name='polloption_add', brief="Adds a poll option to vote for.", description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private messages. The status of the poll must be \'CLOSED\' to use this command.\nThis command adds a option with name to vote for into the poll with the given ID. You can only add up to 7 options.The number of the option is always the lowest available.\nAs an input you need the poll ID, which you can get with \"+polls\", and the option Name. When you want a option with spaces in it, then set the name in \"\". The name can not be longer than 112 characters.')
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

	@commands.command(name='polloption_remove', brief='Removes an option from a poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private messages. The status of the poll must be \'CLOSED\' to use this command.\nThis command removes a option with the spefified name for the poll with the given ID.\nAs an input you need the poll ID, which you can get with \"+polls\", and the option Name, which you can get with \"+poll pollID\".')
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

	@commands.command(name='polls', brief='Gives a brief list of all polls.', description='You need to be a \'member\', \'Administrator\', \'moderator\' or \'friend\' to use this command. Can only be used in private messages or in te spam-channel.\nThis command shows you the header of all stored polls.')
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

	@commands.command(name='poll_remove', brief='Removes a poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private messages.\nThis command removes a poll completely from the storage. Can only be used if the poll is cloesed. Also it is not possible for users with no PrivilegeLevel to remove a poll while it has options. A message will then be send to an authorized to remove to poll. \nAs an input you need the poll ID, which you can get with \"+polls\".')
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


	@commands.command(name='poll_open', brief='Opens a poll for votes.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used text-channels other than \'level\', \'info\', \'log\'. The status of the poll must be \'CLOSED\' or \'OPEN\' to use this command.\nThis command will post the poll (as seen in \'+poll\') to the text-channel. If the poll is already \'OPEN\' the previous version will be deleted from the channel and reposted. Also reactions will be added to vote with. You can change your vote as often as you like.This can sometimes break if to many users vote at once without waiting for reactions to be added. \nAs an input you need the poll ID, which you can get with \"+polls\".')
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
		await ctx.message.delete()

	@commands.command(name='poll_close', brief='Closes a poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used in private channels. The status of the poll must be \'OPEN\' to use this command.\nThis command will close a poll again. Then yo are free to manipulate the poll. \nAs an input you need the poll ID, which you can get with \"+polls\".')
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

	@commands.command(name='poll_publish', brief='Publish a poll.', description='You need to be a \'member\', \'Administrator\' or \'moderator\' to use this command. Can only be used text-channels other than \'level\', \'info\', \'log\'. The status of the poll must be \'OPEN\' to use this command.\nThis command will post the finished poll to the text channel and will be ordered by the amount of votes. The previously opened poll will be delete. \nAs an input you need the poll ID, which you can get with \"+polls\".')
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