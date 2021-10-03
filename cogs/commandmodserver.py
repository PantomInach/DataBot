import discord
from discord.utils import get
from discord.ext import commands
import asyncio

from helpfunctions.utils import Utils
from datahandler.textban import Textban
from datahandler.counter import Counter
from datahandler.jsonhandel import Jsonhandel

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
			if Commandmodserver.utils.hasOneRole(args[1].author.id, [*items]):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

class Commandmodserver(commands.Cog, name='Server Mod Commands'):
	"""
	Currently unused
	"""

	utils = None

	def __init__(self, bot):
		super(Commandmodserver, self).__init__()
		self.bot = bot
		self.jh = Jsonhandel()
		self.tban = Textban()
		self.jh = Jsonhandel
		self.utils = Utils(bot, jh = self.jh)
		self.counter = Counter()
		Commandmodserver.utils = self.utils

def setup(bot):
	bot.add_cog(Commandmodserver(bot))
