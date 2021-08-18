import asyncio
import discord
from discord.ext import commands
from .jsonhandel import Jsonhandel
from .helpfunc import Helpfunc

"""
Following functions are ment to use as decorators, when not using @commands.command
"""

def isBotOwner():
	def decorator(func):
		def wrapper(*args, **kwargs):
			jh = Jsonhandel()
			if jh.getPrivilegeLevel(args[1].author.id) >= 2:
				return func(*args, **kwargs)
			return sendCTX(args[1], "Not permitted")
		return wrapper
	return decorator

def isBotMod():
	def decorator(func):
		def wrapper(*args, **kwargs):
			jh = Jsonhandel()
			if jh.getPrivilegeLevel(args[1].author.id) >= 1:
				return func(*args, **kwargs)
			return sendCTX(args[1], "Not permitted")
		return wrapper
	return decorator

def isDM():
	def decorator(func):
		def wrapper(*args, **kwargs):
			if isinstance(args[1].channel, discord.channel.DMChannel):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isInChannel(*items):
	def decorator(func):
		def wrapper(*args, **kwargs):
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if not dm and (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isInChannelOrDM(*items):
	def decorator(func):
		def wrapper(*args, **kwargs):
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if dm or args[1].channel.id in items or args[1].channel.name in items:
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isNotInChannel(*items):
	def decorator(func):
		def wrapper(*args, **kwargs):
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if dm or not (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isNotInChannelOrDM(*items):
	def decorator(func):
		def wrapper(*args, **kwargs):
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if not dm or not (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator


async def sendCTX(ctx, message):
	await ctx.send(message)

async def passFunc():
	await asyncio.sleep(0)








"""
Following functions are ment to use as decorators, when using @commands.command
"""
def isBotModCommand():
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 1
	return commands.check(predicate)

def isBotOwnerCommand():
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 2
	return commands.check(predicate)

def isDMCommand():
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel)
	return commands.check(predicate)

def isInChannelCommand(*items):
	"""
	Checks if Command is invoked in a channel configured in items.
	"""
	def predicate(ctx):
		if isinstance(ctx.channel, discord.channel.DMChannel):
			return False
		return ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isInChannelOrDMCommand(*items):
	"""
	Checks if Command is invoked in a channel configured in items or a DM.
	"""
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isNotInChannelCommand(*items):
	def predicate(ctx):
		return not (ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)

def isNotInChannelOrDMCommand(*items):
	def predicate(ctx):
		return not (isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)
