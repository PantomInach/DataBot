import discord
from discord.utils import get
from discord.ext import commands
from .decorators import *
import asyncio

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
			if Commandpoll.helpf.hasOneRole(args[1].author.id, [*items]):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

class Commandmodserver(commands.Cog, name='Server Mod Commands'):
	"""
	Currently unused
	"""

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
