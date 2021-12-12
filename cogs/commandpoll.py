import discord
from discord.ext import commands

from helpfunctions.decorators import isDMCommand, isInChannelOrDMCommand, isNotInChannelOrDMCommand
from helpfunctions.utils import Utils
from datahandler.poll import Poll
from datahandler.jsonhandel import Jsonhandel

def hasAnyRole(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Check if a user has any of the roles in items.

	Only use for commands, which USE @commands.command
	commands.has_any_role() does not work in DM since a users can't have roles.
	This on pulls the roles from the configured guilde and makes the same check as commands.has_any_role().

	Function is not in decorators.py since the Helpfunction Object is needed.
	"""
	def predicate(ctx):
		return Commandpoll.utils.hasOneRole(ctx.author.id, [*items])
	return commands.check(predicate)

class Commandpoll(commands.Cog, name='Poll Commands'):
	"""
	This bot has the option to host polls. Here is how to do it:

	1) Create a poll:
		You can create a poll by 'poll create [poll name]'.
		The poll name musst be smaller than 71 characters and will be the title of the poll.
		You will get a overview of the poll back. This also includes the poll id, which will be important to configure the poll.
	1.1) List poll:
		With 'poll list' you will get a overview of every poll the bot knows about.
	2) Add options:
		Use 'poll op add [poll id] [option name]' to add a option to your poll.
		The option name musst be smaller than 113 characters and will be displayed in the poll.
	2.1) Remove option:
		If you want to remove a option than it will be possible with 'poll op rm [poll id] [option name]'.
	3) View your poll:
		To check if every thing is all right with your poll you can use 'poll show [poll id]'.
		This will give you the poll like it will be posted.
	4) Open your poll:
		Now that your are ready with your poll, you can use 'poll open [poll id]' to make it available to vote for in the channel you wrote the command.
		The member votes will the updated live in the poll, but every thing is anonymous.
		You can only open your poll if in the overview stands that your poll is closed.
	5) Edit your poll:
		Maybe you spot a typo or want to change the poll. Than use the command 'poll close [poll id]' to close the poll.
		This resultes in RESETING your poll. So proceed with caution. Also the poll will be deleted from the channel.
		Now you can use 'poll op add [poll id] [option name]' and 'poll op rm [poll id] [option name]' to modify it.
		Just use 'poll open [poll id]' to reopen it.
	6) Publish your poll:
		Times up. You want to publish the resultes. So you need to use 'poll publish [poll id]'.
		This will post the finished poll in the channel.
	"""
	"""
	These Commands define interactions with polls.
	"""

	utils = None

	def __init__(self, bot):
		super(Commandpoll, self).__init__()
		self.bot = bot
		self.poll = Poll()
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		Commandpoll.utils = self.utils

	@commands.group(name = 'poll')
	async def poll(self, ctx):
		"""
		Group of poll commands.

		This command group is for creating and managing polls. 

		How to 'poll':
		1) Create a poll: 	'poll create [poll name]'
		1.1) List polls:	'poll list'
		2) Add option:		'poll op add [poll id] [option name]'
		2.1) Remove option:	'poll op rm [poll id] [option name]'
		3) View poll:		'poll show [poll id]'
		4) Open poll:		'poll open [poll id]'
		5) Close poll:		'poll close [poll id]'
		6) Publish poll:	'poll publish [poll id]'
		7) Remove poll:		'poll rm [poll id]'

		For a more indept explanation for using the poll command use 'help Poll Commands'.

		List of all commands with poll:
			poll create [poll id]
			poll list
			poll op add [poll id] [option name] 
			poll op rm [poll id] [option name]
			poll show [poll id]
			poll open [poll id]
			poll close [poll id]
			poll publish [poll id]
			poll rm [poll id]

		More infos can be found via 'help poll [command]'.

		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'poll' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: create, list, show, close, open ,publish, rm, op", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help poll'")
			await ctx.send(embed = embed, delete_after = 3600)

	@poll.command(name = 'create', brief = 'Creates a poll.')
	@isDMCommand()
	@hasAnyRole("CEO","COO","chairman")
	async def pollCreate(self, ctx, pollName):
		"""
		You can create a poll by 'poll create [poll name]'.
		The poll name musst be smaller than 71 characters and will be the title of the poll.
		You will get a overview of the poll back. This also includes the poll id, which will be important to configure the poll.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'. 
		"""
		"""
		param ctx:	Discord Context object.
		param pollName:	String.

		Creates a poll with the given name.
		Poll will have the lowest possible ID.

		Sends a overwiew of the poll.
		"""
		message = ""
		if len(pollName) <= 71:
			pollID = self.poll.newPoll(pollName)
			datum = self.poll.getDate(pollID)
			status = self.poll.getStatus(pollID)
			sumVotes = self.poll.getSumVotes(pollID)
			message = f"```md\n{pollID}\t{pollName}\t{datum}\t{status}\t{sumVotes}\n```\n"
			await self.utils.log(f"User {ctx.author} created the poll {pollName} with ID: {pollID}.",1)
		else:
			message = "ERROR: The optionName is to long."
		await ctx.send(message)

	@poll.command(name = 'show', brief = 'Shows a poll.')
	@isDMCommand()
	@hasAnyRole("CEO","COO","chairman")
	async def pollShow(self, ctx, pollID):
		"""
		To check if every thing is all right with your poll you can use 'poll show [poll id]'.
		This will give you the poll like it will be posted.
		Poll id can be look up with 'poll list'.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'. 
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json

		Sends the poll with options to the user.
		Does not change status. Only as a preview.
		"""
		message = ""
		if self.poll.isAPollID(pollID):
			message = self.poll.pollString(pollID)
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@poll.group(name = 'op', briefe = 'Manipulate options of a poll.')
	@isDMCommand()
	@hasAnyRole("CEO","COO","chairman")
	async def optioneParent(self, ctx):
		"""
		Group of poll option commands.

		With this command group you can add and remove poll options.

		More infos can be found via 'help poll op [command]'. 

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'. 
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'poll op' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: add, rm", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help poll op'")
			await ctx.send(embed = embed, delete_after = 3600)


	@optioneParent.command(name = 'add', brief = 'Add potion to a poll')
	async def optionAdd(self, ctx, pollID, optionName):
		"""
		Use 'poll op add [poll id] [option name]' to add a option to your poll.
		The option name will be displayed in the poll.

		Can onyl be used if the poll is closed.
		The option name musst be smaller than 113 characters and there can only be 7 options.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'. 
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json
		param optionName:	String.

		Trys to add a option to the poll with optionName.
		New option gets lowest possible optionID.
		"""
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


	@optioneParent.command(name = 'rm', brief = 'Remove a option from a poll.')
	async def polloptionRemove(self, ctx, pollID, optionName):
		"""
		If you want to remove a option than it will be possible with 'poll op rm [poll id] [option name]'.

		Can onyl be used if the poll is closed.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'. 
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json
		param optionName:	String.

		Trys to remove a option from the poll with optionName.
		All ids from options higher than the removed option will decremented.
		"""
		message = ""
		if self.poll.isAPollID(pollID):
			if not self.poll.optionRemove(pollID, str(optionName)):
				message = "ERROR: Could not find option Name or poll is not CLOSED. Try another Name.\n"
			message += f"{self.poll.pollString(pollID)}"
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@poll.command(name = 'list', brief = 'Gives Overview of all polls.')
	@isInChannelOrDMCommand("🚮spam")
	@hasAnyRole("CEO","COO","chairman","associate")
	async def pollsList(self, ctx):
		"""
		With 'poll list' you will get a overview of every poll the bot knows about.
		This includes 'poll id', 'poll name', 'date of creation', 'status' and 'votes'.

		Can only be used in the DM with the bot or in the '🚮spam' channel and only by users with one of the roles 'CEO', 'COO', 'chairman' or 'associate'.
		"""
		"""
		param ctx:	Discord Context object.

		Sends the header of all polls in poll.json.
		"""
		message = ""
		for pollID in self.poll.getAllPolls()[::-1]:
			message += self.poll.pollHeader(pollID)
		if message == "":
			message = "No active polls."
		await ctx.send(message)

	@poll.command(name = 'rm', brief = 'Removes a poll.')
	@isDMCommand()
	@hasAnyRole("CEO","COO","chairman")
	async def poll_remove(self, ctx, pollID):
		"""
		To add an option to a poll use the command 'poll op add [poll id] [option name]'

		Can onyl be used if the poll is closed.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'.
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json

		Removes a poll from poll.json if requirements are meet.
		"""
		message = ""
		if self.poll.isAPollID(pollID):
			pollName = self.poll.getName(pollID)
			if len(self.poll.getOptions(pollID)) == 0 or self.jh.getPrivilegeLevel(ctx.author.id) >= 1 or self.utils.hasRole(ctx.author.id, "chairman"):
				if self.poll.removePoll(pollID):
					message = f"Removed Poll {pollName}."
					await self.utils.log(f"User {ctx.author.mention} removed the poll: \"{pollName}\".", 2)
					channel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
					server = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
					await channel.send(f"User {ctx.author.mention} removed the poll: \"{pollName}\".")
				else:
					message = "ERROR: Something strange happend."
					await self.utils.log(f"User {ctx.author.name} tried to remove poll: \"{pollName}\", {pollID} with message: {ctx.message.content}")
			else:
				message = "Can't remove a poll with options. Contacted Bot Mods to review your command. The poll will maybe be removed."
				await self.utils.sendServerModMessage(f"User {ctx.author.mention} wants to removed the poll: \"{pollName}\". Use Command \"+poll_remove {pollID}.\" to remove to poll.")
		else:
			message = "ERROR: Poll does not exists. Check +polls for active polls."
		await ctx.send(message)

	@poll.command(name = 'open', brief = 'Opens a poll.')
	@isNotInChannelOrDMCommand("📂log","📢info","⏫level")
	@hasAnyRole("CEO","COO","chairman")
	async def poll_open(self, ctx, pollID):
		"""
		To open a poll use the command 'poll open [poll id]'.
		The poll will be posted like in 'poll show' to the channel, in which the command is invoked.
		Also reactions will be added, which enable a member to vote on the option.
		Votes will be shown in real time in the poll.

		Can onyl be used if the poll is closed.

		Can not be used in the "📂log","📢info","⏫level" channel or DM with the bot and can be only by users with one of the roles 'CEO', 'COO' or 'chairman'.
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json

		Posts a poll to channel, adds reactions to vote for options and opens poll.
		"""
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
			await self.utils.log(f"User {ctx.author.mention} opened the poll {pollID} in channel {ctx.channel.name}.",1)
		elif self.poll.getStatus(pollID) == "CLOSED":
			message = f"ERROR: You can't open a poll with only 1 polloption"
			await ctx.author.send(message)
		await ctx.message.delete()

	@poll.command(name = 'close', brief = 'Closes a poll.')
	@isDMCommand()
	@hasAnyRole("CEO","COO","chairman")
	async def poll_close(self, ctx, pollID):
		"""
		Closing a poll can be done by the command 'poll close [poll id]'.
		Now the poll can be edited again via 'poll op add/rm'.
		Also the posted poll will be edited to show that it is closed and the reactions will be removed.

		Can onyl be used if the poll is open.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO', 'COO' or 'chairman'.
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json

		Sets status of poll to closed and removes reactions from poll, so nobody can vote anymore.
		"""
		[messageID, channelID] = self.poll.getMessageID(pollID)
		if self.poll.pollClose(pollID) and messageID and channelID:
			channel = self.bot.get_channel(int(channelID))
			message = await channel.fetch_message(int(messageID))
			if message != None:
				await message.clear_reactions()
				await message.edit(content=f"{self.poll.pollString(pollID)}")
				# self.poll.setMessageID(pollID, '', '')
				await self.utils.log(f"User {ctx.author.name} cloesed poll: \"{self.poll.getName(pollID)}\"",1)
		else:
			await ctx.send("ERROR: Can't close Poll")	

	@poll.command(name = 'publish', brief = 'Publishes a poll.')
	@isNotInChannelOrDMCommand("📂log","📢info","⏫level")
	@hasAnyRole("CEO","COO","chairman")
	async def poll_publish(self, ctx, pollID):
		"""
		To publish a poll use the command 'poll publish [poll id]'.
		The poll will be posted like in 'poll show' to the channel, in which the command is invoked.
		Published polls can not be altert and give the final resulte of a poll.

		Can onyl be used if the poll is open.

		Can not be used in the "📂log","📢info","⏫level" channel or DM with the bot and can be only by users with one of the roles 'CEO', 'COO' or 'chairman'.
		"""
		"""
		param ctx:	Discord Context object.
		param pollID:	Integer. ID of a poll in poll.json

		Sets status of poll to published and removes reactions from poll, so nobody can vote anymore.
		"""
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

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		"""
		param payload:	Gives context about the added reaction

		Handels diffrent bot interactions with the server via ractions.

		First:
			Handles leaderboard interactions for new page and new sorting.
		Second:
			Handels voting on polls.
		Third:
			Give role on data processing.
		Forth: (Handel here)
			Handels ractions on interest groups for user the get roles.
		Fifth:
			Give XP when a reaction is added.
		Sixth:
			Give role of giveRoles message.
		"""	

		# Ignore bot reactions
		if self.bot.get_user(payload.user_id).bot:
			return

		userID = payload.user_id
		channel = self.bot.get_channel(int(payload.channel_id))
		message = await channel.fetch_message(int(payload.message_id))
		[state, page] = Utils.getMessageState(message)
		"""
		State (0,0): Normal Message
		State (1,x): Leaderboard sorted by XP on page x
		State (2,x): Leaderboard sorted by Voice on page x
		State (3,x): Leaderboard sorted by TextCount on page x
		State (4,0): Poll
		State (5,0): data protection declaration
		State (6,0): giveRoles message
		"""

		if state == 4:
			# Number which option was voted. New reaction => -1
			newVote = self.votedOption(message)

			# Checks if user is allowed to vote and is valid
			if self.utils.hasRole(userID, "employee") and newVote != -1:
				# changes poll message
				pollID = int(str(message.content)[6:10])
				optionName = self.poll.getOptionByNumber(pollID, newVote+1)
				self.poll.addUserVote(pollID, userID, optionName)
				await message.edit(content=f"{self.poll.pollString(pollID)}")

			# Removes member vote
			await message.remove_reaction(payload.emoji, payload.member)

	"""
	"""

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

def setup(bot):
	bot.add_cog(Commandpoll(bot))