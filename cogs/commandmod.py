import discord
from discord.ext import commands

from helpfunctions.decorators import isBotModCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.jsonhandel import Jsonhandel

class Commandmod(commands.Cog, name='Bot Mod Commands'):
	"""
	Group of 'Bot Mod' commands.

	Commands to manage no critical settings of the bot.
	 
	List of commands:
		textwl add (channelID)
		textwl rm (channelID)
		voicebl add (channelID)
		voicebl rm (channelID)
		dp

	More infos can be found via 'help textwl', 'help voicebl' and 'help dp'.

	The list of commands below you can execute in this channel.
	"""
	def __init__(self, bot):
		super(Commandmod, self).__init__()
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		self.xpf = Xpfunk()


	"""
	######################################################################

	Text Whitlist commands and function

	######################################################################
	"""

	@commands.group(name = 'textwl', brief = 'Add or remove a text channel to be logged by the bot.')
	@isBotModCommand()
	async def textwl(self, ctx):
		"""
		Group of text whitlist commands.

		This command group is for managing the text whitlist.
		When a message is sent to a text channel on the whitlist, which the bot can see, the author of this message will get XP.

		Use \'textwl add [channelID]\' or use \'textwl add\' in a channel to add it to the whitlist.
		Use \'textwl rm [channelID]\' or use \'textwl rm\' in a channel to remove it from the whitlist.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.

		More infos can be found via 'help textwl [command]'.

		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'textwl' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: add, remove", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help textwl'")
			await ctx.send(embed = embed, delete_after = 3600)

	@textwl.command(name = 'add', brief = 'Adds a channel to the whitlist')
	async def addtextwhitelist(self, ctx, channelID = None):
		"""
		Adds a text channel to the whitlist.

		You can obtain the channel id by right clicking on a channel and pressing 'copy id' when you have developer options enabled.
		Also it is possible to add a text channel to the whitlist by writting 'textwl add' into it.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channels ID. Default is None.

		Adds channel to whitlist so users can get XP in the channel.
		"""
		guilde = self.bot.get_guild(self.jh.getFromConfig("guilde"))
		channels = self.bot.guilds[0].text_channels
		# When channelID is not given, use ctx.channel.id.
		if not channelID:
			channelID = ctx.channel.id
		# Test if channel is in Server
		if str(channelID) in [str(channel.id) for channel in channels]:
			#Try to write in whitelist
			if self.jh.writeToWhitelist(channelID):
				channelName = str(self.bot.get_channel(int(channelID)))
				message = f"Added {channelName} with id {channelID} to Whitelist. This Text channel will be logged."
			else:
				message = "Channel is already in Whitelist."
		else:
			message = f"Channel is not in the server {str(guilde)}"
			await self.utils.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	@textwl.command(name = 'rm', brief = 'Removes a text channel from the whitlist')
	async def removetextwhitelist(self, ctx, channelID = None):
		"""
		Removes a text channel from the whitlist.

		You can obtain the channel id by right clicking on a channel and pressing 'copy id' when you have developer options enabled.
		Also it is possible to remove a text channel from the whitlist by writting 'textwl rm' into it.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channels ID. Default is None.

		Removes channel from whitlist so users can not get XP in the channel.
		"""
		# When channelID is not given, use ctx.channel.id.
		if not channelID:
			channelID = ctx.channel.id
		# Try to remove from whitelist
		if self.jh.removeFromWhitelist(channelID):
			channelName = str(self.bot.get_channel(int(channelID)))
			message = f"Removed {channelName} with id {channelID} from Whitelist. This Text channel will not be logged."
		else:
			message = "Channel does not exist or is not in Whitelist"
			await self.utils.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	"""
	######################################################################

	Voice Blacklist commands and function

	######################################################################
	"""

	@commands.group(name='voicebl')
	@isBotModCommand()
	async def voicebl(self, ctx):
		"""
		Group of voice blacklist commands.

		This command group is for managing the voice blacklist.
		In a predefined time intervall the bot scannes all voice channel for member to give them XP. When the channel is on the blacklist, it will be ignored. 

		Use \'voicelb add [channelID]\' to add a channel to the blacklist.
		Use \'voicelb rm [channelID]\' to remove it from the blacklist.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.

		More infos can be found via 'help voicebl [command]'.

		The list of commands below you can execute in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Is the parent command for the 'voicebl' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: add, remove", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help voicebl'")
			await ctx.send(embed = embed, delete_after = 3600)

	@voicebl.command(name = 'add', brief = 'Add a voice channel to the blacklist.')
	async def addblacklist(self, ctx, channelID):
		"""
		Adds a voice channel to the blacklist.

		You can obtain the channel id by right clicking on a channel and pressing 'copy id' when you have developer options enabled.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channels ID.

		Adds channel to whitlist so users can not get XP in the channel.
		"""
		guilde = self.bot.get_guild(self.jh.getFromConfig("guilde"))
		channels = self.bot.guilds[0].voice_channels
		#Test if channel is in Server
		if str(channelID) in [str(channel.id) for channel in channels]:
			#Try to write in Blacklist
			if self.jh.writeToBalcklist(channelID):
				channelName = str(self.bot.get_channel(int(channelID)))
				message = f"Added {channelName} with id {channelID} to Blacklist. This Voice channel will not be logged."
			else:
				message = "Channel is already in Blacklist."
		else:
			message = f"Channel is not in the server {str(guilde)}"
		await self.utils.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	@voicebl.command(name = 'rm', brief = 'Removes a voice channel from the blacklist.')
	async def removeblacklist(self, ctx, channelID = None):
		"""
		Removes a voice channel from the blacklist.

		You can obtain the channel id by right clicking on a channel and pressing 'copy id' when you have developer options enabled.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channels ID. Default is None.

		Removes channel from whitlist so users can get XP in the channel.
		"""
		# When channelID is not given, use ctx.channel.id.
		if not channelID:
			channelID = ctx.channel.id
		if self.jh.removeFromBalcklist(channelID):
			channelName = str(self.bot.get_channel(int(channelID)))
			message = f"Removed {channelName} with id {channelID} from Blacklist. This Voice channel will be logged."
		else:
			message = "Channel does not exist or is not in Blacklist"
		await self.utils.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	"""
	######################################################################

	Normal @commads.command functions

	######################################################################
	"""

	@commands.command(name='dp', brief='Prints the Data of the Users')
	@isBotModCommand()
	async def printData(self,ctx):
		"""
		Prints the Username, userID, level, voiceXP, textXP and textCount off all members on the server.
		If user is not in the guilde anymore the name will be replaced by 'No User'.

		Can only be used by bot mods aka user with a privilage level of 1 or higher.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Prints all user data in format:
			User: "User name", UserID: UserID, Level: int, VoiceXP: int, TextXP: int, Messages: int.
		"""
		guilde = str(self.bot.get_guild(int(self.jh.getFromConfig("guilde"))))
		message = f"Printing data of server {guilde}:\n"
		# Sorts user by there usernames
		sortedData = sorted(self.jh.data, key = lambda id: str(self.bot.get_user(int(id)).name).lower() if self.bot.get_user(int(id)) != None else "no user")
		for userID in sortedData:
			level = self.jh.getUserLevel(userID)
			voiceXP = self.jh.getUserVoice(userID)
			textXP = self.jh.getUserText(userID)
			textCount = self.jh.getUserTextCount(userID)
			user = self.bot.get_user(int(userID))
			username = "No User"
			#Handel not existing UserIDs
			if user != None:
				username = user.name
			# Message format
			messageadd = f"\nUser: {username}, UserID: {userID}, Level: {level}, VoiceXP: {voiceXP}, TextXP: {textXP}, Messages: {textCount}."
			if len(message)+len(messageadd)>2000: #Get around 2000 char discord text limit
				await ctx.send(message)
				message = ""
			message += messageadd
		print(f"User {ctx.author} prints all data in {ctx.channel}.")	
		await ctx.send(message)


def setup(bot):
	bot.add_cog(Commandmod(bot))