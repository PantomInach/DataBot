import discord
from discord.utils import get
from discord.ext import commands
from .jsonhandel import Jsonhandel
from .xpfunk import Xpfunk
from .helpfunc import Helpfunc
from .inspiro import Inspiro


class Commanduser(commands.Cog, name='User Commands'):
	"""These Commands are available for all users."""
	def __init__(self, bot, helpf, jh, xpf):
		super(Commanduser, self).__init__()
		self.bot = bot
		self.helpf = helpf
		self.jh = jh
		self.xpf = xpf
	
	@commands.command(name='level', pass_context=True, brief='Returns the level of a player.', description='You need privilege level 0 to use this command. Returns the users level on the configured server. The higher the level, the more roles you will get. Can only be used in the level Channel')
	async def getLevel(self, ctx):
		if str(ctx.channel.id) == str(self.jh.getFromConfig("levelchannel")):
			userID = ctx.author.id
			server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
			member = server.get_member(int(userID))
			self.jh.addNewDataEntry(userID)
			#Create Embeded
			avatar_url = ctx.author.avatar_url
			level = self.jh.getUserLevel(userID)
			voiceXP = self.jh.getUserVoice(userID)
			textXP = self.jh.getUserText(userID)
			textCount = self.jh.getUserTextCount(userID)
			nextLevel = self.xpf.xpNeed(voiceXP,textXP)
			embed = discord.Embed(title=f"{member.nick}     ({ctx.author.name})", color=12008408)
			embed.set_thumbnail(url=avatar_url)
			embed.add_field(name="HOURS", value=f"{round(int(voiceXP)/30.0,1)}", inline=True)
			embed.add_field(name="MESSAGES", value=f"{str(textCount)}", inline=True)
			embed.add_field(name="EXPERIENCE", value=f"{str(int(voiceXP)+int(textXP))}/{nextLevel}",inline=True)
			embed.add_field(name="LEVEL", value=f"{level}", inline=True)
			#Send Embeded
			await ctx.send(embed=embed, delete_after=86400)
		if not isinstance(ctx.channel, discord.channel.DMChannel):
			await ctx.message.delete()

	@commands.command(name='top',brief='Sends an interactive rank list.', description='You need privilege level 0 to use this command. Sends a list of the top 10 users orderd by XP. By klicking on ⏫, you jump to the first page, on ⬅, you go one page back, on ➡, you go one page further, on ⏰, you order by time, on 💌, you order by messages sent, and on 🌟, you order by XP. Can only be used in the level Channel')
	async def leaderboard(self, ctx):
		if str(ctx.channel.id) == str(self.jh.getFromConfig("levelchannel")) or (isinstance(ctx.channel, discord.channel.DMChannel) and int(self.jh.getPrivilegeLevel(ctx.author.id)) >= 1):
			await self.helpf.log(f"+top by {ctx.author}",1) #Notify Mods
			#Create leaderboard
			text = f"{await self.helpf.getLeaderboardXBy(0,1)}{ctx.author.mention}"
			message = await ctx.send(text, delete_after=86400)
			reactionsarr = ["⏫","⬅","➡","⏰","💌"]
			for emoji in reactionsarr:
				await message.add_reaction(emoji)
		if not isinstance(ctx.channel, discord.channel.DMChannel):
			await ctx.message.delete()

	@commands.command(name='quote', brief='Sends an unique inspirational quote.', description='You need privilege level 0 to use this command. Sends a random quote from inspirobot.me. Can only be used in the Spam Channel.')
	async def getPicture(self, ctx):
		if str(ctx.channel.id) == str(self.jh.getFromConfig("spamchannel")):
			inspiro = Inspiro()
			url = inspiro.getPictureUrl()
			#Create Embeded
			embed = discord.Embed(color=12008408)
			embed.set_image(url=url)
			embed.set_footer(text=url)
			await ctx.send(content=ctx.author.mention, embed=embed)
		if not isinstance(ctx.channel, discord.channel.DMChannel):
			await ctx.message.delete()

	"""
	@commands.command(name='reclaimData')
	async def reclaimData(self, ctx, voice, text, textCount, code, hash):
		if isinstance(ctx.channel, discord.channel.DMChannel):
			server = self.bot.get_guild(int(self.jh.getFromConfig("server")))
			if server.get_member(ctx.author.id) != None:
				if str(voice).isDigit() and str(text).isDigit() and str(textCount).isDigit() and str(code).isDigit():
					if self.helpf.hashDataWithCode(int(voice), int(text), int (textCount), int(code))[0] == hash:
						self.jh.setUserVoice(ctx.user.id, voice)
						self.jh.setUserText(ctx.user.id, text)
						self.jh.setUserTextCount(ctx.user.id, textCount)
						await ctx.send("You got your data back. The level and level specific will be updated shortly.")
					else:
						await ctx.send(f"ERROR: hash does not match data.")
				else:
					await ctx.send(f"ERROR: you are not on the server.")
			else:
				await ctx.send(f"ERROR: invalid input.")
		else:
			await ctx.message.delete()
	"""

	@commands.command(name='meme')
	async def memeResponse(self, ctx):
		message = "Lieber User,\nder Command nach dem du suchst ist '+ meme'.\nAn die Person, die sich gedacht hat, es sei eine gute Idee das Prefix von Dankmemer Bot soll '+' sein, you suck.\nDer Bot hat gesprochen!"
		await ctx.send(message)
		
def setup(bot, helpf, jh, xpf):
	bot.add_cog(Commandmod(bot, helpf, jh, xpf))