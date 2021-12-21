import discord
import sys
import os
import asyncio
from discord.ext import commands

from discord.utils import find

from helpfunctions.decorators import isBotModCommand, isBotOwnerCommand, isDMCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.textban import Textban
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
		return Commandowner.utils.hasOneRole(ctx.author.id, [*items])
	return commands.check(predicate)

class Commandowner(commands.Cog, name='Bot Owner Commands'):
	"""
	You need privilage level 2 to use these commands.
	Only for development and Bot Owner.
	"""
	def __init__(self, bot):
		super(Commandowner, self).__init__()
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		self.xpf = Xpfunk()
		self.tban = Textban()

		Commandowner.utils = self.utils

	@commands.command(name='test', pass_context=True, brief='Testing command for programmer.', description='You need privilege level Owner to use this command. Only the programmer knows what happens here.')
	@isBotOwnerCommand()
	async def test(self, ctx, inputs):
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		category = find(lambda cat: cat.name == "Subserver Gateway", guild.categories)
		main_gateway = find(lambda vc: vc.name.startswith("Main Server"), category.voice_channels)
		print(main_gateway)
		await main_gateway.edit(name = 'Main Server ' + inputs)

	@commands.command(name="ping")
	@isBotOwnerCommand()
	async def ping(self, ctx):
		await ctx.send("pong pong")

	#Starts to log the users in voice channels
	@commands.command(name='startlog', brief='Starts to log the users on the configured server.', description='You need privilege level 2 to use this command. Gets the connected users of the configured server und increments every minute their voice XP.')
	@isBotOwnerCommand()
	async def startlog(self, ctx):
		if self.jh.getFromConfig("log") == "False":
			self.jh.config["log"] = "True"
			self.jh.saveConfig()
			guildeID = int(self.jh.getFromConfig("guilde"))
			guildeName = str(self.bot.get_guild(guildeID))
			await self.utils.log(f"Start to log users from Server:\n\t{guildeName}",2)
		else:
			await ctx.send(f"Bot is logging. Logging state: True")

	@commands.command(name='stoplog', brief='Stops to log the users on configured server.', description='You need privilege level 2 to use this command. When the bot logs the connective users on the configured server, this command stops the logging process.')
	@isBotOwnerCommand()
	async def stoplog(self, ctx):
		if self.jh.getFromConfig("log")=="True":
			guildeID = int(self.jh.getFromConfig("guilde"))
			guildeName = str(self.bot.get_guild(guildeID))
			self.jh.config["log"] = "False"
			self.jh.saveConfig()
			await self.utils.log(f"Stopped to log users from Server:\n\t{guildeName}",2)
		else:
			await ctx.send(f"Bot is NOT logging. Logging state: False")

	@commands.command(name='stopbot', brief='Shuts down the bot.', description='You need privilege level 2 to use this command. This command shuts the bot down.')
	@isBotOwnerCommand()
	async def stopbot(self, ctx):
		await self.utils.log("[Shut down] Beginning shutdown...",2)
		# Save json files
		self.jh.saveConfig()
		self.jh.saveData()
		await self.utils.log("[Shut down] Files saved",2)
		# Remove all textbans
		self.tban.removeAllTextBan()
		await self.utils.log("[Shut down] Bot is shutdown",2)
		#await self.bot.logout()
		await self.bot.close()

	@commands.command(name='sendDPD', brief='Sends data protection declaration to channel')
	@isBotOwnerCommand()
	async def sendDPD(self, ctx):
		datapath = str(os.path.dirname(__file__))[:-4]+"/data/"
		string = ""
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		lenght = len(guilde.members)
		i = 0
		with open(datapath+"dataProtection.txt","r") as f:
			string = f.read()
		for member in guilde.members:
			await self.utils.removeRoles(member.id, ["chairman", "associate", "employee", "rookie"])
			print(f"Progress: {i}/{lenght}")
			i = i+1
		message = await ctx.send(string)
		await message.add_reaction("✅")

	@commands.command(name='sendGR', brief='Sends message to assing roles')
	@isBotOwnerCommand()
	async def sendGiveRoles(self, ctx):
		text = "**Choose your interest group**\n```You will be given roles based on your interest that grant you access to optional voice- and textchannels.\nInterest:                      Rolename:\n🎮 gaming                      gaming\n📚 study-channel               student\n👾 development-technology      dev-tech\n🏹 single-exchange             single\n🤑 gambling-channel            gambling\n⚡ bot-development             bot-dev```"
		guilde = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))
		lenght = len(guilde.members)
		i = 1
		for member in guilde.members:
			await self.utils.removeRoles(member.id, ["gaming", "student", "dev-tech", "single", "gambling", "bot-dev"])
			print(f"Progress: {i}/{lenght}")
			i = i+1
		message = await ctx.send(string)
		reactionsarr = ["🎮","📚","👾","🏹","🤑","⚡"]
		for emoji in reactionsarr:
			await message.add_reaction(emoji)

	@commands.command(name='changeBotMessage')
	@isBotOwnerCommand()
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
	@isBotOwnerCommand()
	async def addReaction(self, ctx, channelID, messageID, emoji):
		message = await self.bot.get_channel(int(channelID)).fetch_message(int(messageID))
		if (message.author != self.bot.user):
			await ctx.send("Message is not from bot.")
			return
		try:
			await message.add_reaction(emoji)
		except InvalidArgument:
			await ctx.send("No vaild emoji was sent by user.")

	@commands.command(name = 'rlext')
	@isBotOwnerCommand()
	async def reloadExtensions(self, ctx, *extensions):
		"""
		Reloads cogs.
		"""
		"""
		param ctx:	Discord Context object.
		param *ext:	Names of extensions to be reloaded.

		Reloads given extensions so changes are taken over.
		When no extension is given, all extensions will be reloaded.
		"""
		if not extensions:
			extensions = self.bot.extensions.copy()
			list(extensions.keys()).extend(["cogs." + ext[:-3] for ext in os.listdir("./") if ext.endswith(".py")])
		reloadedExtensions = []
		for ext in extensions:
			if ext in self.bot.extensions:
				self.bot.unload_extension(ext)
				self.bot.load_extension(ext)
				reloadedExtensions.append(ext)
		await self.utils.log(f"Reloaded extensions: {', '.join(reloadedExtensions)}", 2)

	@commands.group(name = 'hahahah')
	@isBotOwnerCommand()
	@hasAnyRole("gaming")
	async def testing(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("No subcommand is invoked 2")
		else:
			await ctx.send("Invoking subcommand")
		

	@testing.command()
	@isDMCommand()
	async def sub(self, ctx, *inputs):
		await ctx.send(" ".join(inputs) + "Geht")

def setup(bot):
	bot.add_cog(Commandowner(bot))