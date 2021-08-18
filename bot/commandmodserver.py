import discord
from discord.utils import get
from discord.ext import commands
from .decorators import *
import asyncio

def hasAnyRole(*items):
		"""
		commands.has_any_role() does not work in DM since a users can't have roles.
		This on pulls the roles from the conffigured guilde and makes the same check as commands.has_any_role().
		"""
		def predicate(ctx):
			return Commandmodserver.helpf.hasOneRole(ctx.author.id, [*items])
		return commands.check(predicate)

class Commandmodserver(commands.Cog, name='Server Mod Commands'):
	"""docstring for Commandmodserver"""

	helpf = None

	def __init__(self, bot, helpf, tban, counter, jh):
		super(Commandmodserver, self).__init__()
		self.bot = bot
		self.tban = tban
		self.jh = jh
		self.helpf = helpf
		Commandmodserver.helpf = helpf

def setup(bot, helpf, tban, jh):
	bot.add_cog(Commandpoll(bot, helpf, tban, jh))
