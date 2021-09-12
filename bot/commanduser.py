import discord
from discord.utils import get
from discord.ext import commands
from .inspiro import Inspiro
from .decorators import *


def hasAnyRole(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Check if a user has any of the roles in items.

	Only use for commands, which don't use @commands.command
	commands.has_any_role() does not work in DM since a users can't have roles.
	This on pulls the roles from the configured guilde and makes the same check as commands.has_any_role().

	Function is not in decorators.py since the Bot or Helpfunction Object is needed.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			if Commanduser.helpf.hasOneRole(args[1].author.id, [*items]):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

class Commanduser(commands.Cog, name='User Commands'):
	"""
	Class defines user specific commands and functions, which are executed by bot commands.

	Commands:
		user
		level
		meme
	"""

	helpf = None

	def __init__(self, bot, helpf, tban, jh, xpf):
		super(Commanduser, self).__init__()
		# Defines all needed objects
		self.bot = bot
		self.helpf = helpf
		self.jh = jh
		self.tban = tban
		self.xpf = xpf
		# For hasAnyRole Decorator
		Commanduser.helpf = helpf

	@commands.command(name='user')
	async def userCommandsInterpretor(self, ctx, *inputs):
		"""
		param ctx:	Discord Context object. Automatical passed.
		param inputs:	Tuple of arguments of commands.

		Interpretes send commands beginning with user and calls the right function.
		"""
		lenght = len(inputs)
		if lenght == 2 and inputs[0] == "get":
			await self.getUserData(ctx, inputs[1])

		elif lenght == 2 and inputs[0] == "rm":
			await self.removeuser(ctx, inputs[1])

		elif lenght == 4 and inputs[0] == "set" and inputs[1] == "tc":
			await self.setTextCount(ctx, inputs[2], inputs[3])

		elif lenght == 4 and inputs[0] == "set" and inputs[1] == "text":
			await self.setTextXP(ctx, inputs[2], inputs[3])

		elif lenght == 4 and inputs[0] == "set" and inputs[1] == "voice":
			await self.setVoiceXP(ctx, inputs[2], inputs[3])

		elif lenght == 4 and inputs[0] == "tb" and inputs[1] == "add":
			await self.textban(ctx, inputs[2], inputs[3], inputs[4])

		elif lenght == 3 and inputs[0] == "tb" and inputs[1] == "rm":
			await self.textunban(ctx, inputs[2])

		else:
			await ctx.author.send(f"Command \"user {' '.join(inputs)}\" is not valid.")



	"""
	######################################################################

	Bot Mod user commands

	######################################################################
	"""

	@isBotMod()
	async def getUserData(self, ctx, userID):
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

	@isBotMod()
	async def setVoiceXP(self, ctx, userID, amount):
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
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} voiceXP to {amount}.",2)
		await ctx.send(message)

	@isBotMod()
	async def setTextXP(self, ctx, userID, amount):
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
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textXP to {amount}.",2)
		await ctx.send(message)

	@isBotMod()
	async def setTextCount(self, ctx, userID, amount):
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
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textCount to {amount}.",2)
		await ctx.send(message)

	@isBotMod()
	async def removeuser(self, ctx, userID):
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
		await self.helpf.log(f"User {ctx.author}: {message}",2)
		await ctx.send(message)



	"""
	######################################################################

	Guilde Mod user commands

	######################################################################
	"""

	@isDM()
	@hasAnyRole("CEO","COO")
	async def textban(self, ctx, userID, time, reason):
		"""
		param ctx:	Discord Context object.
		param userID:	Is the userID from discord user as a String or int
		param time:	Duration of ban as float. Musst be over 0.1.
		param reason:	Reason for textban.

		Textbans a user by adding them to textban.json.
		Textbans are carryed out in main.on_message() by deleting send messages.
		"""
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
					await self.helpf.log(f"User {ctx.author.mention} textbaned {user.mention} for {time} h. Reason:\n{reason}",2)
					await logchannel.send(f"{user.mention} was textbaned for {time} h.\n**Reason**: {reason}")
					await user.send(content=f"You received a textban for {time} h.\n**Reason**: {reason}")
					await self.helpf.sendServerModMessage(f"{member.nick} ({user.name}) was textbaned by {guilde.get_member(int(ctx.author.id)).nick} ({ctx.author.name}) for {time} h.\n**Reason**: {reason}")
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
					

	@isDM()
	@hasAnyRole("CEO","COO")
	async def textunban(self, ctx, userID):
		if not self.tban.hasTextBan(ctx.author.id):
			if self.tban.removeTextBan(userID):
				logchannel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
				user = self.bot.get_user(int(userID))
				await self.helpf.log(f"User {ctx.author.mention} textunbaned {user.mention}",2)
				await logchannel.send(f"User {ctx.author.mention} textunbaned {user.mention}")
			else:
				await ctx.send(content="ERROR: User has no textban.", delete_after=3600)


	"""
	######################################################################

	Normal @commads.command functions

	######################################################################
	"""

	@commands.command(name='level', pass_context=True, brief='Returns the level of a player.', description='You need privilege level 0 to use this command. Returns the users level on the configured server. The higher the level, the more roles you will get. Can only be used in the level Channel')
	@isInChannelCommand("⏫level")
	async def getLevel(self, ctx):
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

	@commands.command(name='top',brief='Sends an interactive rank list.', description='You need privilege level 0 to use this command. Sends a list of the top 10 users orderd by XP. By klicking on ⏫, you jump to the first page, on ⬅, you go one page back, on ➡, you go one page further, on ⏰, you order by time, on 💌, you order by messages sent, and on 🌟, you order by XP. Can only be used in the level Channel')
	@isInChannelCommand("⏫level")
	async def leaderboard(self, ctx):
		"""
		param ctx:	Discord Context object.

		Creates a leaderboard and posts it with the emojis to manipulate it.
		"""
		await self.helpf.log(f"+top by {ctx.author}",1) #Notify Mods
		#Create leaderboard
		text = f"{self.helpf.getLeaderboardPageBy(0,1)}{ctx.author.mention}"
		message = await ctx.send(text, delete_after=86400)
		reactionsarr = ["⏫","⬅","➡","⏰","💌"]
		for emoji in reactionsarr:
			await message.add_reaction(emoji)
		await ctx.message.delete()

	@commands.command(name='quote', brief='Sends an unique inspirational quote.', description='You need privilege level 0 to use this command. Sends a random quote from inspirobot.me. Can only be used in the Spam Channel.')
	@isInChannelCommand("🚮spam")
	async def getPicture(self, ctx):
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
					if self.helpf.hashDataWithCode(int(voice), int(text), int (textCount), int(code))[0] == hash:
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

	@commands.command(name='meme')
	async def memeResponse(self, ctx):
		"""
		param ctx:	Discord Context object.

		Rebellion againt some special person.
		!!! Not for production !!!
		"""
		message = "Lieber User,\nder Command nach dem du suchst ist '+ meme'.\nAn die Person, die sich gedacht hat, es sei eine gute Idee das Prefix von Dankmemer Bot soll '+' sein, you suck.\nDer Bot hat gesprochen!"
		await ctx.send(message)

		
def setup(bot, helpf, jh, xpf):
	bot.add_cog(Commandmod(bot, helpf, jh, xpf))