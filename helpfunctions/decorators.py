import asyncio
import discord
from discord.ext import commands
from datahandler.jsonhandel import Jsonhandel
from helpfunctions.helpfunc import Helpfunc

"""
Following functions are ment to use as decorators, when not using @commands.command
"""

def isBotOwner():
	"""
	Type:	Decorator for functions with ctx object in args[1].

	Checks if a user has a Bot privilage level of 2 or higher.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			jh = Jsonhandel()
			if jh.getPrivilegeLevel(args[1].author.id) >= 2:
				return func(*args, **kwargs)
			return sendCTX(args[1], "Not permitted")
		return wrapper
	return decorator

def isBotMod():
	"""
	Type:	Decorator for functions with ctx object in args[1].

	Checks if a user has a Bot privilage level of 1 or higher.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			jh = Jsonhandel()
			if jh.getPrivilegeLevel(args[1].author.id) >= 1:
				return func(*args, **kwargs)
			return sendCTX(args[1], "Not permitted")
		return wrapper
	return decorator

def isDM():
	"""
	Type:	Decorator for functions with ctx object in args[1].

	Checks if a message is send in a private channel.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			if isinstance(args[1].channel, discord.channel.DMChannel):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isInChannel(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Checks if a message is send in a channel of *items.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if not dm and (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isInChannelOrDM(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Checks if a message is send in a channel of *items or in a private channel.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if dm or args[1].channel.id in items or args[1].channel.name in items:
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isNotInChannel(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Checks if a message is not send in a channel of *items.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if dm or not (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator

def isNotInChannelOrDM(*items):
	"""
	Type:	Decorator for functions with ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel ids or names.

	Checks if a message is not send in a channel of *items or in a private channel.
	Than executes the function.
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			# Wrapper for inputs in func
			dm = isinstance(args[1].channel, discord.channel.DMChannel)
			if not dm or not (args[1].channel.id in items or args[1].channel.name in items):
				return func(*args, **kwargs)
			return passFunc()
		return wrapper
	return decorator


async def sendCTX(ctx, message):
	"""
	param ctx:	Discord Context Object
	param message:	String.

	Sends message to channel of ctx's origin.
	Helpfunction for Decorators for error messages.
	"""
	await ctx.send(message)

async def sendAuthor(ctx, message):
	"""
	param ctx:	Discord Context Object
	param message:	String.

	Sends message to author of ctx.
	Helpfunction for Decorators for error messages.
	"""
	await ctx.author.send(message)

async def passFunc():
	"""
	Helpfunction to not execute function in failed checks of Decorators.
	"""
	await asyncio.sleep(0)








"""
Following functions are ment to use as decorators, when using @commands.command
"""

def isBotModCommand():
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a user has a Bot privilage level of 2 or higher.
	"""
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 1
	return commands.check(predicate)

def isBotOwnerCommand():
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a user has a Bot privilage level of 1 or higher.
	"""
	def predicate(ctx):
		jh = Jsonhandel()
		return jh.getPrivilegeLevel(ctx.author.id) >= 2
	return commands.check(predicate)

def isDMCommand():
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a message is send in a private channel.
	"""
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel)
	return commands.check(predicate)

def isInChannelCommand(*items):
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a message is send in a channel of *items.
	"""
	def predicate(ctx):
		if isinstance(ctx.channel, discord.channel.DMChannel):
			return False
		return ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isInChannelOrDMCommand(*items):
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a message is send in a channel of *items or in a private channel.
	"""
	def predicate(ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items
	return commands.check(predicate)

def isNotInChannelCommand(*items):
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a message is not send in a channel of *items.
	"""
	def predicate(ctx):
		return not (ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)

def isNotInChannelOrDMCommand(*items):
	"""
	Type:	Decorator of @commands.command Bot functions.

	Checks if a message is not send in a channel of *items or in a private channel.
	"""
	def predicate(ctx):
		return not (isinstance(ctx.channel, discord.channel.DMChannel) or ctx.channel.id in items or ctx.channel.name in items)
	return commands.check(predicate)
