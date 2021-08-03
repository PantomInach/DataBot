import discord
import sys
import os
from discord.utils import get
from discord.ext import commands
from .decorators import *
import asyncio

class Commandowner(commands.Cog, name='Bot Owner Commands'):
	"""You need privilage level 2 to use these commands."""
	def __init__(self, bot, helpf, tban, jh, xpf):
		super(Commandowner, self).__init__()
		self.bot = bot
		self.helpf = helpf
		self.jh = jh
		self.xpf = xpf
		self.tban = tban

	@commands.command(name='test', pass_context=True, brief='Testing command for programmer.', description='You need privilege level Owner to use this command. Only the programmer knows what happens here.')
	@isBotOwner()
	async def test(self, ctx):
		await ctx.send("Geht")		

	@commands.command(name="ping")
	@isBotOwner()
	async def ping(self, ctx):
		await ctx.send("pong")

	#Starts to log the users in voice channels
	@commands.command(name='startlog', brief='Starts to log the users on the configured server.', description='You need privilege level 2 to use this command. Gets the connected users of the configured server und increments every minute their voice XP.')
	@isBotOwner()
	async def startlog(self, ctx):
		if self.jh.getFromConfig("log") == "False":
			self.jh.config["log"] = "True"
			self.jh.saveConfig()
			guildeID = int(self.jh.getFromConfig("server"))
			guildeName = str(self.bot.get_guild(guildeID))
			await self.helpf.log(f"Start to log users from Server:\n\t{guildeName}",2)
			while self.jh.getFromConfig("log"):
				self.helpf.addMembersOnlineVoiceXp(guildeID)
				await self.helpf.levelAkk()
				await self.helpf.updateRoles()
				self.jh.saveData()
				await asyncio.sleep(120)
		else:
			await ctx.send(f"Bot is logging. Logging state: True")

	@commands.command(name='stoplog', brief='Stops to log the users on configured server.', description='You need privilege level 2 to use this command. When the bot logs the connective users on the configured server, this command stops the logging process.')
	@isBotOwner()
	async def stoplog(self, ctx):
		if self.jh.getFromConfig("log")=="True":
			guildeID = int(self.jh.getFromConfig("server"))
			guildeName = str(self.bot.get_guild(guildeID))
			self.jh.config["log"] = "False"
			self.jh.saveConfig()
			await self.helpf.log(f"Stopped to log users from Server:\n\t{guildeName}",2)
		else:
			await ctx.send(f"Bot is NOT logging. Logging state: False")

	@commands.command(name='stopbot', brief='Shuts down the bot.', description='You need privilege level 2 to use this command. This command shuts the bot down.')
	@isBotOwner()
	async def stopbot(self, ctx):
		self.jh.saveConfig()
		self.jh.saveData()
		self.tban.removeAllTextBan()
		self.helpf.log("Bot is shutdown",2)
		await ctx.bot.logout()
		await bot.close()
		sys.exit()

	@commands.command(name='sendDPD', brief='Sends data protection declaration to channel')
	@isBotOwner()
	async def sendDPD(self, ctx):
		binpath = str(os.path.dirname(__file__))[:-4]+"/bin/"
		string = ""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		lenght = len(guilde.members)
		i = 0
		with open(binpath+"dataProtection.txt","r") as f:
			string = f.read()
		for member in guilde.members:
			await self.helpf.removeRoles(member.id, ["chairman", "associate", "employee", "rookie"])
			print(f"Progress: {i}/{lenght}")
			i = i+1
		message = await ctx.send(string)
		await message.add_reaction("✅")

	@commands.command(name='sendGR', brief='Sends message to assing roles')
	@isBotOwner()
	async def sendGiveRoles(self, ctx):
		text = "**Choose your interest group**\n```You will be given roles based on your interest that grant you access to optional voice- and textchannels.\nInterest:                      Rolename:\n🎮 gaming                      gaming\n📚 study-channel               student\n👾 development-technology      dev-tech\n🏹 single-exchange             single\n🤑 gambling-channel            gambling\n⚡ bot-development             bot-dev```"
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		lenght = len(guilde.members)
		i = 1
		for member in guilde.members:
			await self.helpf.removeRoles(member.id, ["gaming", "student", "dev-tech", "single", "gambling", "bot-dev"])
			print(f"Progress: {i}/{lenght}")
			i = i+1
		message = await ctx.send(string)
		reactionsarr = ["🎮","📚","👾","🏹","🤑","⚡"]
		for emoji in reactionsarr:
			await message.add_reaction(emoji)

	@commands.command(name='changeBotMessage')
	@isBotOwner()
	async def changeBotMessage(self, ctx, channelID, messageID, text):
		message = await self.bot.get_channel(int(channelID)).fetch_message(int(messageID))
		if (message.author != self.bot.user):
			await ctx.send("Message is not from bot.")
			return
		if len(text) > 2000:
			await ctx.send(f"Text is to long")
			return
		await message.edit(content=str(text))

	@commands.command(name='addReaction')
	@isBotOwner()
	async def addReaction(self, ctx, channelID, messageID, emoji):
		message = await self.bot.get_channel(int(channelID)).fetch_message(int(messageID))
		if (message.author != self.bot.user):
			await ctx.send("Message is not from bot.")
			return
		try:
			await message.add_reaction(emoji)
		except InvalidArgument:
			await ctx.send("No vaild emoji was sent by user.") 

def setup(bot, helpf, jh, xpf):
	bot.add_cog(Commandmod(bot, helpf, tban, jh, xpf))