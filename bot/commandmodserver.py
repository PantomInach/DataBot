import discord
from discord.utils import get
from discord.ext import commands
from .textban import Textban
from .jsonhandel import Jsonhandel
from .helpfunc import Helpfunc
from .counter import Counter
import asyncio

class Commandmodserver(commands.Cog, name='Server Mod Commands'):
	"""docstring for Commandmodserver"""
	def __init__(self, bot, helpf, tban, counter, jh):
		super(Commandmodserver, self).__init__()
		self.bot = bot
		self.tban = tban
		self.jh = jh
		self.helpf = helpf

	#Checks if cahnnel is a PM channel
	def isPM(self, ctx):
		return isinstance(ctx.channel, discord.channel.DMChannel)

	#Checks if author has member, admin or mod rigths
	async def hasRights(self, ctx):
		server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
		userID = ctx.author.id
		member = server.get_member(userID)
		for roll in ["CEO", "COO"]:
			if await self.helpf.hasRole(userID, roll):
				return True
		return False

	@commands.command(name='textban', brief='Textbans a user.', description='You need to be a \'Administrator\' or \'moderator\' to use this command. Can only be used in a private channel and \'log\'.\nAdds a user to the textban-list. The users text-messages will be deletet upon posting them. You can not change the ban time, only unban with \'+textunban\'.\nTo use this command you need the userID, which you can get be rigth-clicking on the person. Also a time is requiered. The time you input will be in seconds. Also a reason is requiered. The reason must be in \"\", otherwise the command wont work.')
	async def textban(self, ctx, userID, time, reason):
		pm = self.isPM(ctx)
		logID = self.jh.getFromConfig("logchannel")
		if pm or ctx.channel.id == int(logID):
			if await self.hasRights(ctx):
				if not self.tban.hasTextBan(userID):
					bantime = 0
					try:
						bantime = float(time)
					except ValueError:
						bantime = -1
					if bantime >= 0.1:
						user = self.bot.get_user(int(userID))
						server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
						member = server.get_member(int(userID))
						if user != None:
							logchannel = self.bot.get_channel(int(logID))
							if not pm:
								await ctx.message.delete()
							await self.helpf.log(f"User {ctx.author.mention} textbaned {user.mention} for {time} h. Reason:\n{reason}",2)
							await logchannel.send(f"{user.mention} was textbaned for {time} h.\n**Reason**: {reason}")
							await user.send(content=f"You received a textban for {time} h.\n**Reason**: {reason}")
							await self.helpf.sendServerModMessage(f"{member.nick} ({user.name}) was textbaned by {server.get_member(int(ctx.author.id)).nick} ({ctx.author.name}) for {time} h.\n**Reason**: {reason}")
							await self.tban.addTextBan(userID, int(bantime*3600.0))
							#Textban over
							await user.send("Your Textban is over. Pay more attention to your behavior in the future.")
						else:
							await ctx.send(content="ERROR: User does not exist.", delete_after=3600)
					else:
						await ctx.send(content="ERROR: time is not valid.", delete_after=3600)
				else:
					await ctx.send(content="ERROR: User has already a textban.", delete_after=3600)
			elif not pm:
				await ctx.message.delete()
		if not pm:
			await ctx.message.delete()
					

	@commands.command(name='textunban', brief='Removes textban from user.', description='You need to be a \'Administrator\' or \'moderator\' to use this command. Can only be used in a private channel and \'log\'.\nThis command will remnove a person from the textban-list and the messages from the person wont be removed anymore.\nTo use this command you need the userID, which you can get be rigth-clicking on the person.')
	async def textunban(self, ctx, userID):
		pm = self.isPM(ctx)
		logID = self.jh.getFromConfig("logchannel")
		if pm or ctx.channel.id == logID:
			if await self.hasRights(ctx) and not self.tban.hasTextBan(ctx.author.id):
				if self.tban.removeTextBan(userID):
					logchannel = self.bot.get_channel(int(logID))
					user = self.bot.get_user(int(userID))
					await self.helpf.log(f"User {ctx.author.mention} textunbaned {user.mention}",2)
					await logchannel.send(f"User {ctx.author.mention} textunbaned {user.mention}")
				else:
					await ctx.send(content="ERROR: User has no textban.", delete_after=3600)
			elif not pm:
				await ctx.message.delete()
		if not pm:
			await ctx.message.delete()

def setup(bot, helpf, tban, jh):
	bot.add_cog(Commandpoll(bot, helpf, tban, jh))
