import discord
from discord.utils import find
from discord.ext import commands

from helpfunctions.inspiro import Inspiro
from helpfunctions.decorators import isBotModCommand, isDMCommand, isInChannelCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.textban import Textban
from datahandler.sub import Sub
from datahandler.jsonhandel import Jsonhandel

import datetime
import time

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
		return Commanduser.utils.hasOneRole(ctx.author.id, [*items])
	return commands.check(predicate)

class Commanduser(commands.Cog, name='User Commands'):
	"""
	Class defines user specific commands and functions, which are executed by bot commands.

	Commands:
		user get [user id]
		user rm [user id]
		user set tc [user id] [amount]
		user set text [user id] [amount]
		user set voice [user id] [amount]
		user star [user id]
		user tb give [user id] [time] (reason)
		user tb rm [user id]
		level
		top
		star

	More infos can be found via 'help [command]'.

	The list of commands below you can execute in this channel.
	"""

	utils = None

	def __init__(self, bot):
		super(Commanduser, self).__init__()
		# Defines all needed objects
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		self.tban = Textban()
		self.xpf = Xpfunk()
		self.sub = Sub()
		# For hasAnyRole Decorator
		Commanduser.utils = self.utils

	@commands.group(name='user', brief = 'Group of user commands.')
	async def userParent(self, ctx):
		"""
		Used to manage users via the bot.

		Commands:
			user get:	Gives an overview of stored data from the user.
			user rm:	Removes the user data from the stored data.
			user set:	Can set the ex specific data of a user.
			user star:	Gives user 'star of the week' role.
			user tb:	Manages Textbans of users.

		More infos can be found via 'help [command]'.
	
		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'user' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: get, rm, set, tb, star", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help user'")
			await ctx.send(embed = embed, delete_after = 3600)
		
	"""
	######################################################################

	Bot Mod user commands

	######################################################################
	"""

	@userParent.group(name = 'set', brief = 'Group of user set commands.')
	@isBotModCommand()
	async def userSetParent(self, ctx):
		"""
		This command is used to set the voicexp, textxp, textcount of users.
		Commands:
			user set tc 	=> sets textcount
			user set voice	=> sets voicexp
			user set text 	=> sets textxp

		Can only be used by bot mods aka user with a privilage level of 1 or higher.

		More infos can be found via 'help [command]'.
	
		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'user set' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: voice, text, tc", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help user set'")
			await ctx.send(embed = embed, delete_after = 3600)

	@userParent.command(name = 'get', brief = 'Gets brief infos os users data.')
	@isBotModCommand()
	async def getUserData(self, ctx, userID):
		"""
		This command gives you the voicexp, textxp and textcount of a user via 'user get [user id]'.
		As an input the user id is needed.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		Command: poll get <userID>

		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int

		Sends the user data into the channel.
		"""
		if self.jh.isInData(userID):
			voice = self.jh.getUserVoice(userID)
			text = self.jh.getUserText(userID)
			textCount = self.jh.getUserTextCount(userID)
			message = f"User: {str(self.bot.get_user(int(userID)))} VoiceXP: {voice} TextXP: {text} TextCount: {textCount}"
		else:
			user = self.bot.get_user(int(userID))
			message = f"User was not in data. Created user: {user.mention}"  
		await ctx.send(message)

	@userSetParent.command(name = 'voice', brief = 'Sets users voicexp')
	async def setVoiceXP(self, ctx, userID, amount):
		"""
		Sets users voice xp to given amount via 'user set voice [user id] [amount]'.
		An integer is needed for the amount.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		Command: poll set voice <userID> <amount>

		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int
		param amount:	Integer

		Sets user Voice XP to amount.
		"""
		message = ""
		if not self.jh.isInData(userID):
			message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
			self.jh.addNewDataEntry(userID)
		self.jh.setUserVoice(userID, amount)
		message += f"Set user {str(self.bot.get_user(int(userID)))} voiceXP to {amount}."
		await self.utils.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} voiceXP to {amount}.",2)
		await ctx.send(message)

	@userSetParent.command(name = 'text', brief = 'Sets users textxp.')
	async def setTextXP(self, ctx, userID, amount):
		"""
		Sets users text xp to given amount via 'user set text [user id] [amount]'.
		An integer is needed for the amount.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		Command: poll set text <userID> <amount>

		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int
		param amount:	Integer

		Sets user Text XP to amount.
		"""
		message = ""
		if not self.jh.isInData(userID):
			message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
			self.jh.addNewDataEntry(userID)
		self.jh.setUserText(userID, amount)
		message += f"Set user {str(self.bot.get_user(int(userID)))} textXP to {amount}."
		await self.utils.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textXP to {amount}.",2)
		await ctx.send(message)

	@userSetParent.command(name = 'tc', brief = 'Sets users text count')
	async def setTextCount(self, ctx, userID, amount):
		"""
		Sets users text count to given amount via 'user set tc [user id] [amount]'.
		An integer is needed for the amount.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		Command: poll set tc <userID> <amount>

		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int
		param amount:	Integer

		Sets user Text Count to amount.
		"""
		message = ""
		if not self.jh.isInData(userID):
			message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
			self.jh.addNewDataEntry(userID)
		self.jh.setUserTextCount(userID, amount)
		message += f"Set user {str(self.bot.get_user(int(userID)))} TextCount to {amount}."
		await self.utils.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textCount to {amount}.",2)
		await ctx.send(message)

	@userParent.command(name = 'rm', brief = 'Removes user from bots data.')
	@isBotModCommand()
	async def removeuser(self, ctx, userID):
		"""
		!!! WARNING !!! THIS ACTION IS NOT REVERSIBLE

		Removes the user data from the bot storage via 'user rm [user id]'.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		Command: poll rm <userID>

		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int

		Removes user from data.
		"""
		if self.jh.removeUserFromData(userID) == 1:
			user = self.bot.get_user(int(userID))
			username = "No User"
			if user != None:
				username = user.name
			message = f"Removed User {username} with ID {userID} from Data."
		else:
			message = f"User with ID {userID} is not in data."
		await self.utils.log(f"User {ctx.author}: {message}",2)
		await ctx.send(message)



	"""
	######################################################################

	Guilde Mod user commands

	######################################################################
	"""

	@userParent.group(name = 'tb', brief = 'Group of user textban commands.')
	@isDMCommand()
	@hasAnyRole("CEO","COO")
	async def user_tb_parent(self, ctx):
		"""
		This group of commands is use to manage user textbans.
		Textbans are carried out by deleting every message the user writtes to tht guilde.

		Commands:
			user tb add [user id] [time] [reason]:	Textbans user
			user tb rm [user id]:			Removes users textban

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO' or 'COO'.

		More infos can be found via 'help [command]'.
	
		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'user tb' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: give, rm", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help user tb'")
			await ctx.send(embed = embed, delete_after = 3600)


	@user_tb_parent.command(name = 'give', brief = 'Textban a user.')
	async def textban(self, ctx, userID, time, reason):
		"""
		Give an user a textban via 'user tb add [user id] [time] [reason]'.
		Time musst be a real number higher equal than '0.1'. 
		E.g. '1.4' for a ban over '1.4' hours.
		The reason can be any text.

		The textbaned user messages will be imidiatly removed by the bot. 

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO' or 'COO'.

		! NOTICE ! Currently the textbans will be removed if the bot is restarted.
		"""
		"""
		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int
		param time:	Duration of ban as float. Musst be over 0.1.
		param reason:	Reason for textban.

		Textbans a user by adding them to textban.json.
		Textbans are carryed out in main.on_message() by deleting send messages.
		"""
		if self.tban.hasTextBan(ctx.author.id):
			await ctx.send(content="ERROR: You aren't allowed to textban users when you have a textban.", delete_after=3600)
			return
		if not self.tban.hasTextBan(userID):
			bantime = 0
			# Convert String time to float.
			try:
				bantime = float(time)
			except ValueError:
				bantime = -1
			if bantime >= 0.1:
				# Get member
				user = self.bot.get_user(int(userID))
				guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
				member = guilde.get_member(int(userID))
				if user != None:
					logchannel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
					# Send messages
					await self.utils.log(f"User {ctx.author.mention} textbaned {user.mention} for {time} h. Reason:\n{reason}",2)
					await logchannel.send(f"{user.mention} was textbaned for {time} h.\n**Reason**: {reason}")
					await user.send(content=f"You received a textban for {time} h.\n**Reason**: {reason}")
					await self.utils.sendServerModMessage(f"{member.nick} ({user.name}) was textbaned by {guilde.get_member(int(ctx.author.id)).nick} ({ctx.author.name}) for {time} h.\n**Reason**: {reason}")
					# Textban user and wait till it is over.
					await self.tban.addTextBan(userID, int(bantime*3600.0))
					#Textban over
					await user.send("Your Textban is over. Pay more attention to your behavior in the future.")
				else:
					await ctx.send(content="ERROR: User does not exist.", delete_after=3600)
			else:
				await ctx.send(content="ERROR: time is not valid.", delete_after=3600)
		else:
				await ctx.send(content="ERROR: User has already a textban.", delete_after=3600)
					
	@user_tb_parent.command(name = 'rm', brief = 'Remove a textban from a user.')
	async def textunban(self, ctx, userID):
		"""
		Remove a textban from a user via 'user tb rm [user id]'.
		Now the user can freely writte messages again.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO' or 'COO'.
		"""
		"""
		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int

		Removes a textban of the given user.
		Textbans are carryed out in main.on_message() by deleting send messages.
		"""
		if not self.tban.hasTextBan(ctx.author.id):
			if self.tban.removeTextBan(userID):
				logchannel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
				user = self.bot.get_user(int(userID))
				await self.utils.log(f"User {ctx.author.mention} textunbaned {user.mention}",2)
				await logchannel.send(f"User {ctx.author.mention} textunbaned {user.mention}")
			else:
				await ctx.send(content="ERROR: User has no textban.", delete_after=3600)


	"""
	# When give star of the week should be queued
	@userParent.command(name = 'star', brief = 'Gives user \'star of the week\'.')
	@isDMCommand()
	@hasAnyRole("CEO","COO")
	async def giveStarOfTheWeek(self, ctx, userID):
		""
		You can give a user 'star of the week' via the command 'user star [user id]'.
		This role should be given as a reward if a user did something great.
		The role will be romved every Monday at 00:00 CET sommer time.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO' or 'COO'.
		""
		""
		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int

		Gives the given user the 'star off the week' role when noone else has the role.
		When someone has the role than it will be queued to the next Monday when noone gets the role.
		""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		role = find(lambda role: role.name == "star of the week", guild.roles)
		if role and userID.isdigit() and guild.get_member(int(userID)):
			user = self.bot.get_user(int(userID))
			if role.members:
				# Get next monday in Unix Epoch
				timeWhenNothingInQueue = self._nextWeekdayInUnixEpoch(0)
				# When someone has already the role => Queue in subroutine to give role
				timeString = self.sub.queueGiveRoleOnceAfter(int(userID), role.id, 604800, timeWhenNothingInQueue)
				await self.utils.log(f"User {ctx.author.name} {ctx.author.id} queued {user.name} {user.id} for 'star of the week' on the {timeString}.", 2)
				await ctx.send(f"Member {user.name} will get 'star of the week' on the {timeString}.")

			else:
				# When no one has the role => Give user 'star of the week' immediately
				await self.utils.giveRoles(userID, [role.id])
				await self.utils.log(f"User {ctx.author.name} {ctx.author.id} gave {user.name} {user.id} 'star of the week' threw. +user star ", 2)
				await ctx.send(f"Member {user.name} got 'star of the week' now.")
		else:
			await ctx.send(f"Invalid input. Either userID is not from user of the guild {guild.name} or it is not a ID.")
	"""

	@userParent.command(name = 'star', brief = 'Gives user \'star of the week\'.')
	@isDMCommand()
	@hasAnyRole("CEO", "COO")
	async def giveStarOfTheWeekNow(self, ctx, userID):
		"""
		You can give a user 'star of the week' via the command 'user star [user id]'.
		This role should be given as a reward if a user did something great.
		The role will be romved every Monday at 00:00 CET sommer time.

		Can only be used in the DM with the bot and only by users with one of the roles 'CEO' or 'COO'.
		"""
		"""
		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int

		Gives the given user the 'star off the week' role when noone else has the role.
		When someone has the role do nothing.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		role = find(lambda role: role.name == "star of the week", guild.roles)
		if role and userID.isdigit() and guild.get_member(int(userID)):
			user = self.bot.get_user(int(userID))
			if role.members:
				# Print Error
				await ctx.send(f"Someone already has the role 'star of the week'.")

			else:
				# When no one has the role => Give user 'star of the week' immediately
				await self.utils.giveRoles(userID, [role.id])
				await self.utils.log(f"User {ctx.author.name} {ctx.author.id} gave {user.name} {user.id} 'star of the week' threw. +user star ", 2)
				await ctx.send(f"Member {user.name} got 'star of the week' now.")

	def _nextWeekdayInUnixEpoch(self, toWeekday):
		"""
		param weekday:	Which next weekday to output. In [0,6]

		Takes current date and returns next weekday in Unix Epoch.
		"""
		today = datetime.date.today()
		nextWeekday = today + datetime.timedelta(days=-today.weekday() + toWeekday, weeks=1)
		return time.mktime(time.strptime(f"{nextWeekday.year} {nextWeekday.month} {nextWeekday.day}", "%Y %m %d"))



	"""
	######################################################################

	Normal @commads.command functions

	######################################################################
	"""

	@commands.command(name='level', pass_context=True, brief='Returns the level of a player.')
	@isInChannelCommand("⏫level")
	async def getLevel(self, ctx):
		"""
		Gives the user a level card via the command 'level'.
		This gives a short overview over your stats on the guilde.

		Can only be used in "⏫level" channel.
		"""
		"""
		param ctx:	Discord Context object.

		Creates a embeded level card of user.
		"""
		userID = ctx.author.id
		server = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		member = server.get_member(int(userID))
		self.jh.addNewDataEntry(userID)
		#Create Embeded
		avatar_url = ctx.author.avatar_url
		level = self.jh.getUserLevel(userID)
		voiceXP = self.jh.getUserVoice(userID)
		textXP = self.jh.getUserText(userID)
		textCount = self.jh.getUserTextCount(userID)
		nextLevel = self.xpf.xpNeed(voiceXP,textXP)
		embed = discord.Embed(title=f"{member.nick}     ({ctx.author.name})", color=12008408)
		embed.set_thumbnail(url=avatar_url)
		embed.add_field(name="HOURS", value=f"{round(int(voiceXP)/30.0,1)}", inline=True)
		embed.add_field(name="MESSAGES", value=f"{str(textCount)}", inline=True)
		embed.add_field(name="EXPERIENCE", value=f"{str(int(voiceXP)+int(textXP))}/{nextLevel}",inline=True)
		embed.add_field(name="LEVEL", value=f"{level}", inline=True)
		#Send Embeded
		await ctx.send(embed=embed, delete_after=86400)
		await ctx.message.delete()

	@commands.command(name='top',brief='Sends an interactive rank list.')
	@isInChannelCommand("⏫level")
	async def leaderboard(self, ctx):
		"""
		Spawns an interavtive leaderboard in the "⏫level" via the command 'top'.
		Displays the first 10 member with the highest xp total.
		The sites can be changed via reacting with the ⬅️ ➡️ emojis. Use ⬅️ to go higher und ➡️ to go lower.
		With ⏫ you get again to the first page.

		Normaly the leaderboard is sorted by the total xp. You can see this if 🕰️ 💌 are reactions.
		When 🌟 🕰️ are available, than it is sorted by messages.
		When 🌟 💌 are available, than it is sorted by time on guilde.
		You can change the sorting by reacting with 🌟 for total xp, 🕰️ for time spent on guilde and 💌 for total messages send.

		Can only be used in the "⏫level" channel.
		"""
		"""
		param ctx:	Discord Context object.

		Creates a leaderboard and posts it with the emojis to manipulate it.
		"""
		await self.utils.log(f"+top by {ctx.author}",1) #Notify Mods
		#Create leaderboard
		text = f"{self.utils.getLeaderboardPageBy(0,0)}{ctx.author.mention}"
		message = await ctx.send(text, delete_after=86400)
		reactionsarr = ["⏫","⬅","➡","⏰","💌"]
		for emoji in reactionsarr:
			await message.add_reaction(emoji)
		await ctx.message.delete()

	@commands.command(name='quote', brief='Sends an unique inspirational quote.')
	@isInChannelCommand("🚮spam")
	async def getPicture(self, ctx):
		"""
		Sent a AI generated inspirational quote via 'quote'.
		This quotes are randomly from 'inspirobot.me'.

		Can only be used in the "🚮spam" channel.
		"""
		"""
		param ctx:	Discord Context object.

		Sents a AI generated quote from inspirobot.me
		"""
		url = Inspiro.getPictureUrl()
		#Create Embeded
		embed = discord.Embed(color=12008408)
		embed.set_image(url=url)
		embed.set_footer(text=url)
		await ctx.send(content=ctx.author.mention, embed=embed)
		await ctx.message.delete()

	"""
	Unsupported

	@commands.command(name='reclaimData')
	async def reclaimData(self, ctx, voice, text, textCount, code, hash):
		if isinstance(ctx.channel, discord.channel.DMChannel):
			server = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
			if server.get_member(ctx.author.id) != None:
				if str(voice).isDigit() and str(text).isDigit() and str(textCount).isDigit() and str(code).isDigit():
					if self.utils.hashDataWithCode(int(voice), int(text), int (textCount), int(code))[0] == hash:
						self.jh.setUserVoice(ctx.user.id, voice)
						self.jh.setUserText(ctx.user.id, text)
						self.jh.setUserTextCount(ctx.user.id, textCount)
						await ctx.send("You got your data back. The level and level specific will be updated shortly.")
					else:
						await ctx.send(f"ERROR: hash does not match data.")
				else:
					await ctx.send(f"ERROR: you are not on the server.")
			else:
				await ctx.send(f"ERROR: invalid input.")
		else:
			await ctx.message.delete()
	"""
		
def setup(bot):
	bot.add_cog(Commanduser(bot))