import discord
from discord.utils import get
from discord.ext import commands
from .jsonhandel import Jsonhandel
from .xpfunk import Xpfunk
from .helpfunc import Helpfunc

class Commandmod(commands.Cog, name='Bot Mod Commands'):
	"""You need privilage level 1 to use these commands."""
	def __init__(self, bot, helpf, jh, xpf):
		super(Commandmod, self).__init__()
		self.bot = bot
		self.helpf = helpf
		self.jh = jh
		self.xpf = xpf

	#Adds channel to blacklist
	@commands.command(name='addvoiceblacklist', brief='Adds a voice channel to the blacklist.', description='You need privilege level 1 to use this command. You can add a voice channel to the blacklist. The users in blacklisted channels will not get voice XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	async def addblacklist(self, ctx, channelID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			server = self.bot.get_guild(self.jh.getFromConfig("server"))
			channels = await self.helpf.channelList(self.jh.getFromConfig("server"))
			#Test if channel is in Server
			if str(channelID) in channels:
				#Try to write in Blacklist
				if self.jh.writeToBalcklist(channelID):
					channelName = str(self.bot.get_channel(int(channelID)))
					message = f"Added {channelName} with id {channelID} to Blacklist. This Voice channel will not be logged."
				else:
					message = "Channel is already in Blacklist."
			else:
				message = f"Channel is not in the server {str(server)}"
		author = ctx.author
		await self.helpf.log(f"{message} from user {author}",2)
		await ctx.send(message)

	#Removes channels from blacklist
	@commands.command(name='removevoiceblacklist', brief='Removes a voice channel to the blacklist.', description='You need privilege level 1 to use this command. You can remove a voice channel from the blacklist. The users in this channel will get voice XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	async def removeblacklist(self, ctx, channelID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			#Try to remove from Blacklist
			if self.jh.removeFromBalcklist(channelID):
				channelName = str(self.bot.get_channel(int(channelID)))
				message = f"Removed {channelName} with id {channelID} from Blacklist. This Voice channel will be logged."
			else:
				message = "Channel does not exist or is not in Blacklist"
		author = ctx.author
		await self.helpf.log(f"{message} from user {author}",2)
		await ctx.send(message)

	#Adds text channel to whitelist
	@commands.command(name='addtextwhitelist', brief='Adds a text channel to the whitelist.', description='You need privilege level 1 to use this command. You can add a text channel to the whitelist. Users writting in channels from the whitelist will get text XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	async def addtextwhitelist(self, ctx, channelID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			server = self.bot.get_guild(self.jh.getFromConfig("server"))
			channels = await self.helpf.channelList(self.jh.getFromConfig("server"))
			#Test if channel is in Server
			if str(channelID) in channels:
				#Try to write in whitelist
				if self.jh.writeToWhitelist(channelID):
					channelName = str(self.bot.get_channel(int(channelID)))
					message = f"Added {channelName} with id {channelID} to Whitelist. This Text channel will be logged."
				else:
					message = "Channel is already in Whitelist."
			else:
				message = f"Channel is not in the server {str(server)}"
		author = ctx.author
		await self.helpf.log(f"{message} from user {author}",2)
		await ctx.send(message)

	#Removes text channel from whitelist
	@commands.command(name='removetextwhitelist', brief='Removes a text channel to the whitelist.', description='You need privilege level 1 to use this command. You can remove text channels from the whitelist. Users writting in channels from the whitelist will get not get text XP. As an input you need the channel id, which you can get by rigth clicking on the channel.')
	async def removetextwhitelist(self, ctx, channelID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			#Try to remove from whitelist
			if self.jh.removeFromWhitelist(channelID):
				channelName = str(self.bot.get_channel(int(channelID)))
				message = f"Removed {channelName} with id {channelID} from Whitelist. This Text channel will not be logged."
			else:
				message = "Channel does not exist or is not in Whitelist"
		author = ctx.author
		await self.helpf.log(f"{message} from user {author}",2)
		await ctx.send(message)

	#TODO: Does not creat new user. Use somehow jh.addNewDataEntry(userID)
	@commands.command(name='getuserdata', brief='Gives VoiceXP, TextXP and writen messages back.', description='You need privilege level 1 to use this command. Returns UserName, UserID, VoiceXP, TextXP and writen messages back. As an input you need the user id, which you can get by rigth clicking on the user.')
	async def getUserData(self, ctx, userID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			if self.jh.isInData(userID):
				userData = self.jh.data[str(userID)]
				voice = userData["Voice"]
				text = userData["Text"]
				textCount = userData["TextCount"]
				message = f"User: {str(self.bot.get_user(int(userID)))} VoiceXP: {voice} TextXP: {text} TextCount: {textCount}"
			else:
				user = self.bot.get_user(int(userID))
				message = f"User was not in data. Created user: {user.mention}"  
		await ctx.send(message)

	#TODO: Does not creat new user. Use somehow jh.addNewDataEntry(userID)
	@commands.command(name='setvoicexp',brief='Sets the voiceXP of a user.', description='You need privilege level 1 to use this command. Sets the voiceXP to the given amount. As an input you need the userID, which you can get by rigth clicking on the user, and the value of the XP.')
	async def setVoiceXP(self, ctx, userID, amount):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			message = ""
			if not self.jh.isInData(userID):
				message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
				self.jh.addNewDataEntry(userID)
			self.jh.data[str(userID)]["Voice"] = str(amount)
			self.jh.saveData()
			message += f"Set user {str(self.bot.get_user(int(userID)))} voiceXP to{amount}."
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} voiceXP to {amount}.",2)
		await ctx.send(message)

	#TODO: Does not creat new user. Use somehow jh.addNewDataEntry(userID)
	@commands.command(name='settextxp',brief='Sets the textXP of a user.', description='You need privilege level 1 to use this command. Sets the TextXP to the given amount. As an input you need the userID, which you can get by rigth clicking on the user, and the value of the XP.')
	async def setTextXP(self, ctx, userID, amount):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			message = ""
			if not self.jh.isInData(userID):
				message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
				self.jh.addNewDataEntry(userID)
			self.jh.data[str(userID)]["Text"] = str(amount)
			self.jh.saveData()
			message += f"Set user {str(self.bot.get_user(int(userID)))} textXP to {amount}."
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textXP to {amount}.",2)
		await ctx.send(message)

	#TODO: Does not creat new user. Use somehow jh.addNewDataEntry(userID)
	@commands.command(name='settextcount',brief='Sets the textCount of a user.', description='You need privilege level 1 to use this command. Sets the TextCount to the given amount. As an input you need the userID, which you can get by rigth clicking on the user, and the value of the XP.')
	async def setTextCount(self, ctx, userID, amount):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			message = ""
			if not self.jh.isInData(userID):
				message = f"User was not in data. Created user: {self.bot.get_user(int(userID))}\n"
				self.jh.addNewDataEntry(userID)
			self.jh.data[str(userID)]["TextCount"] = str(amount)
			self.jh.saveData()
			message += f"Set user {str(self.bot.get_user(int(userID)))} TextCount to {amount}."
		await self.helpf.log(f"User {ctx.author} set user {str(self.bot.get_user(int(userID)))} textCount to {amount}.",2)
		await ctx.send(message)

	@commands.command(name='printdata', brief='Prints the Data of the Users', description='You need privilege level 1 to use this command. Prints the Username, userID, level, voiceXP, textXP and textCount off all users on the server.')
	async def printData(self,ctx):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
			server = str(self.bot.get_guild(int(self.jh.getFromConfig("server"))))
			message = f"Printing data of server {server}:\n"
			# Sorts user by there usernames
			sortedData = sorted(self.jh.data, key = lambda id: str(self.bot.get_user(int(id)).name).lower() if self.bot.get_user(int(id)) != None else "no user")
			for userID in sortedData:
				temp = self.jh.data[str(userID)]
				level = temp["Level"]
				voiceXP = temp["Voice"]
				textXP = temp["Text"]
				textCount = temp["TextCount"]
				user = self.bot.get_user(int(userID))
				username = "No User"
				#Handel not existing UserIDs
				if user != None:
					username = user.name
				messageadd = f"\nUser: {username}, UserID: {userID}, Level: {level}, VoiceXP: {voiceXP}, TextXP: {textXP}, Messages: {textCount}."
				if len(message)+len(messageadd)>2000: #Get around 2000 char discord text limit
					await ctx.send(message)
					message = ""
				message +=messageadd
			print(f"User {ctx.author} prints all data in {ctx.channel}.")	
		await ctx.send(message)

	@commands.command(name='removeuser', brief='Removes user from data.', description='You need privilege level 1 to use this command. Removes the userID from the data und save it. As an input you need the userID, which you can get by rigth clicking on the user.')
	async def removeuser(self, ctx, userID):
		message = "Your are not permitted to use this command. You need Mod privileges"
		if int(self.jh.getPrivilegeLevel(ctx.author.id)) > 0:
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

def setup(bot, helpf, jh, xpf):
	bot.add_cog(Commandmod(bot, helpf, jh, xpf))