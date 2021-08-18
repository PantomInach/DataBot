import discord
from discord.utils import get
from discord.ext import commands
from .decorators import isBotModCommand, isBotMod

class Commandmod(commands.Cog, name='Bot Mod Commands'):
	"""You need privilage level 1 to use these commands."""
	def __init__(self, bot, helpf, jh, xpf):
		super(Commandmod, self).__init__()
		self.bot = bot
		self.helpf = helpf
		self.jh = jh
		self.xpf = xpf


	"""
	######################################################################

	Text Whitlist commands and function

	######################################################################
	"""

	@commands.command(name='textwl')
	@isBotModCommand()
	async def textwlCommandInterpretor(self, ctx, *inputs):
		if inputs[0] == "add":
			await self.addtextwhitelist(ctx, inputs[1])

		elif inputs[0] == "rm":
			await self.removetextwhitelist(ctx, inputs[1])

	#Adds text channel to whitelist
	#@commands.command(name='addtextwhitelist', brief='Adds a text channel to the whitelist.', description='You need privilege level 1 to use this command. You can add a text channel to the whitelist. Users writting in channels from the whitelist will get text XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	#@isBotMod()
	async def addtextwhitelist(self, ctx, channelID):
		guilde = self.bot.get_guild(self.jh.getFromConfig("guilde"))
		channels = self.helpf.getTextChannelsFrom(self.jh.getFromConfig("guilde"))
		#Test if channel is in Server
		if str(channelID) in [str(channel.id) for channel in channels]:
			#Try to write in whitelist
			if self.jh.writeToWhitelist(channelID):
				channelName = str(self.bot.get_channel(int(channelID)))
				message = f"Added {channelName} with id {channelID} to Whitelist. This Text channel will be logged."
			else:
				message = "Channel is already in Whitelist."
		else:
			message = f"Channel is not in the server {str(guilde)}"
			await self.helpf.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	#Removes text channel from whitelist
	#@commands.command(name='removetextwhitelist', brief='Removes a text channel to the whitelist.', description='You need privilege level 1 to use this command. You can remove text channels from the whitelist. Users writting in channels from the whitelist will get not get text XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	#@isBotMod()
	async def removetextwhitelist(self, ctx, channelID):
		#Try to remove from whitelist
		if self.jh.removeFromWhitelist(channelID):
			channelName = str(self.bot.get_channel(int(channelID)))
			message = f"Removed {channelName} with id {channelID} from Whitelist. This Text channel will not be logged."
		else:
			message = "Channel does not exist or is not in Whitelist"
			await self.helpf.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	"""
	######################################################################

	Voice Blacklist commands and function

	######################################################################
	"""

	@commands.command(name='voicebl')
	@isBotModCommand()
	async def voiceblCommandInterpretor(self, ctx, *inputs):
		if inputs[0] == "add":
			await self.addblacklist(ctx, inputs[1])

		elif inputs[0] == "rm":
			await self.removeblacklist(ctx, inputs[1])

	#Adds channel to blacklist
	#@commands.command(name='addvoiceblacklist', brief='Adds a voice channel to the blacklist.', description='You need privilege level 1 to use this command. You can add a voice channel to the blacklist. The users in blacklisted channels will not get voice XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	#@isBotMod()
	async def addblacklist(self, ctx, channelID):
		guilde = self.bot.get_guild(self.jh.getFromConfig("guilde"))
		channels = self.helpf.getVoiceChannelsFrom(self.jh.getFromConfig("guilde"))
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
		await self.helpf.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	#Removes channels from blacklist
	#@commands.command(name='removevoiceblacklist', brief='Removes a voice channel to the blacklist.', description='You need privilege level 1 to use this command. You can remove a voice channel from the blacklist. The users in this channel will get voice XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	#@isBotMod()
	async def removeblacklist(self, ctx, channelID):
		#Try to remove from Blacklist
		if self.jh.removeFromBalcklist(channelID):
			channelName = str(self.bot.get_channel(int(channelID)))
			message = f"Removed {channelName} with id {channelID} from Blacklist. This Voice channel will be logged."
		else:
			message = "Channel does not exist or is not in Blacklist"
		await self.helpf.log(f"{message} from user {ctx.author}",2)
		await ctx.send(message)

	"""
	######################################################################

	Normal @commads.command functions

	######################################################################
	"""

	@commands.command(name='dp', brief='Prints the Data of the Users', description='You need privilege level 1 to use this command. Prints the Username, userID, level, voiceXP, textXP and textCount off all users on the server.')
	@isBotModCommand()
	async def printData(self,ctx):
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
			messageadd = f"\nUser: {username}, UserID: {userID}, Level: {level}, VoiceXP: {voiceXP}, TextXP: {textXP}, Messages: {textCount}."
			if len(message)+len(messageadd)>2000: #Get around 2000 char discord text limit
				await ctx.send(message)
				message = ""
			message += messageadd
		print(f"User {ctx.author} prints all data in {ctx.channel}.")	
		await ctx.send(message)



def setup(bot, helpf, jh, xpf):
	bot.add_cog(Commandmod(bot, helpf, jh, xpf))