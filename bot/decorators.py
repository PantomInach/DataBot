import asyncio
import discord
from discord.ext import commands
from .jsonhandel import Jsonhandel
from .helpfunc import Helpfunc

"""
Following functions are ment to use as decorators
"""
def isBotMod():
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 1
	return commands.check(predicate)

def isBotOwner():
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 2
	return commands.check(predicate)

def isDM():
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel)
	return commands.check(predicate)

def isInChannel(*items):
	"""
	Checks if Command is invoked in a channel configured in items.
	"""
	def predicate(ctx):
		if isinstance(ctx.channel, discord.channel.DMChannel):
			return False
		return ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isInChannelOrDM(*items):
	"""
	Checks if Command is invoked in a channel configured in items or a DM.
	"""
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isNotInChannel(*items):
	def predicate(ctx):
		return not (ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)

def isNotInChannelOrDM(*items):
	def predicate(ctx):
		return not (isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)





