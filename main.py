import certifi
import os
import discord
from discord.utils import get
from discord.ext import commands
import time
import datetime
from bot.jsonhandel import Jsonhandel
from bot.xpfunk import Xpfunk
from bot.helpfunc import Helpfunc
from bot.commanduser import Commanduser
from bot.commandmod import Commandmod
from bot.commandowner import Commandowner
from bot.commandpoll import Commandpoll
from bot.commandmodserver import Commandmodserver
from bot.textban import Textban
import asyncio

print("Prepare to start Bot...")

# Create Objects
jh = Jsonhandel()
xpf = Xpfunk(jh)
poll = Poll()
tban = Textban()
cntr = Counter()

# Create Bot Object
intents = discord.Intents.default()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix = jh.getFromConfig("command_prefix"), intents=intents)

# Create Helpfunctions Object
helpf = Helpfunc(bot, jh, xpf)

print("Objects created")

"""
In the following code there will be the bot.events defined
"""

# When bot is connected
@bot.event
async def on_ready():
	#Sends mesage to mods, when bot is online
    print("Now Online")
    await helpf.sendModsMessage("Bot ist online")

# When bot reads a message
@bot.event
async def on_message(message):
	if (message.author == bot.user):
		return

	# Delet messages if user is textbanned
	if tban.hasTextBan(int(message.author.id)) and not isinstance(message.channel, discord.channel.DMChannel):
		await message.delete()
		return

	a = "" + message.content
	# Stops user from writting in levelchannel none command messages 
	if str(message.channel.id) == str(jh.getFromConfig("levelchannel")) and a[0] != jh.getFromConfig("command_prefix"):
		await message.delete()
		return

	# Checks if message containts a picture
	if len(message.attachments) > 0 and jh.getFromConfig("log")=="True":
		attachments = message.attachments
		userID = message.author.id
		for attachment in attachments:
			name = attachment.filename
			if name[-3:] == "jpg" or name[-3:] == "png":
				# Gives XP when picture is in message
				jh.addTextXP(userID, xpf.randomRange(20,40))
				jh.saveData()
				return

	# When Message is a String
	if a != "" and a[0] != jh.getFromConfig("command_prefix") and jh.getFromConfig("log")=="True":
		# Give XP when message is not a command 
		if jh.isInWhitelist(message.channel_id):
			jh.addTextXP(message.author.id, xpf.textXP(a))
			jh.saveData()

	# Sends BotOwner commands, which are triggering the bot
	if a[0] == jh.getFromConfig("command_prefix"):
		channelName = "DM"
		try:
			channelName = message.channel.name
		except:
			channelName = "DM"
		string = f"\n######\n# User {message.author.name} tried to invoke a command in {channelName}.\n# Command: {a}\n######"
		await helpf.log(string, 2)
	await bot.process_commands(message)

"""
@bot.event 
async def on_disconnect():
	owner = bot.get_user(int(jh.getFromConfig("owner")))
	await helpf.sendOwnerMessage("Bot is offline.")
"""

# When a member joins a guilde
@bot.event
async def on_member_join(member):
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	guilde = bot.get_guild(int(jh.getFromConfig("server")))
	await channel.send(f"Hey **{member.name}**, welcome to {guilde}")


# When a member leaves the guilde
@bot.event
async def on_member_remove(member):
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	guilde = bot.get_guild(int(jh.getFromConfig("server")))
	await channel.send(f"**{member.name}** has left {guilde}. Press F to pay respect.")
	"""
	#Hash user data
	voice = jh.getUserVoice(member.id)
	text = jh.getUserText(member.id)
	textCount = jh.getUserTextCount(member.id)
	[hash, code] = helpf.hashData(voice, text, textCount, member.id)
	#Send user data
	embed = discord.Embed(title=f"{member.nick}     ({member.name})", color=12008408)
	embed.set_thumbnail(url=member.avatar_url)
	embed.add_field(name="VoiceXP", value=f"{voice}", inline=True)
	embed.add_field(name="TextXP", value=f"{text}", inline=True)
	embed.add_field(name="TextMessages", value=f"{textCount}", inline=True)
	embed.add_field(name="Security code", value=f"{code}", inline=False)
	embed.add_field(name="Hash code", value=f"{hash}", inline=False)
	user = await bot.fetch_user(member.id)
	await user.send(content=f"**User related data from {server.name}**", embed=embed)
	await user.send(f"If you would like to join the Server again type this command to gain back your data **after** rejoining the server.\n```+reclaim {voice} {text} {textCount} {code} {hash}```\nhttps://discord.gg/3Fk4gnQ2Jz")
	jh.removeUserFromData(member.id)
	"""

# When a reacting is added
@bot.event
async def on_raw_reaction_add(payload):
	if bot.get_user(payload.user_id).bot:
		return

	userID = payload.user_id
	message = await helpf.getMessageFromPayload(payload)
	[state, page] = helpf.getMessageState(message)
	"""
	State (0,0): Normal Message
	State (1,x): Leaderboard sorted by XP on page x
	State (2,x): Leaderboard sorted by Voice on page x
	State (3,x): Leaderboard sorted by TextCount on page x
	State (4,0): Poll
	State (5,0): data protection declaration
	State (6,0): giveRoles message
	"""
	
	#Stage [1,3] =^= message is Leaderboard
	if state in range(1,4):
		#Handel Leaderboard reactions
		change = helpf.messageToState(message)
		"""
		change:
			0: to first page
			1: page befor
			2: page after
			3: sort xp
			4: sort voice
			5: sort textcount
			6: otherwise
		"""

		if change < 3:
			# Set page if needed
			choice = [0, page-1 if page-1>=0 else 0, page+1]
			page = choice[change]
			# Whip member reaction
			await message.emove_reaction(payload.emoji, payload.member)
		else:
			state = change-3
			# Whip all reactions
			await message.clear_reactions()

		text = helpf.getLeaderboardPageBy(page, state)
		if text == "":
			# If no one is on this page, get last page.
			page -= 1
			text = helpf.getLeaderboardPageBy(page, state)

		# Changes Leaderboard and adds reactions	
		await message.edit(content=f"{text}{payload.member.mention}")
		if change >= 3:
			# When all reactions were whipped
			reactionsarr = ["⏫","⬅","➡","⏰","💌","🌟"]
			removeemoji = [5,3,4]
			del reactionsarr[removeemoji[state-1]]
			for emoji in reactionsarr:
				await message.add_reaction(emoji)

	#State 4 =^= message is poll
	elif state == 4:
		# Number which option was voted. New reaction => -1
		newVote = helpf.votedOption(message)	
		# Checks if user is allowed to vote and is valid
		if helpf.hasRole(userID, "employee") and newVote != -1:
			# changes poll message
			pollID = int(str(message.content)[6:10])
			optionName = poll.getOptionByNumber(pollID, newVote+1)
			poll.addUserVote(pollID, userID, optionName)
			await message.edit(content=f"{poll.pollString(pollID)}")

		# Removes member vote
		await message.remove_reaction(payload.emoji, payload.member)

	# State 5 =^= Note on data processing
	elif state == 5:
		if not helpf.hasRole(userID, "rookie"):
			await helpf.giveRole(userID, "rookie")

	# State 6 =^= User interest groups
	elif state == 6 and (helpf.hasRole(userID, "rookie") or helpf.hasRole(userID, "etwasse")):
		# User needs to accept Note on data processing before using this feature
		# Gives user roll depending on what they react on
		if str(payload.emoji) == "🎮" and not helpf.hasRole(userID, "gaming"):
			await helpf.giveRole(userID, "gaming")
		elif str(payload.emoji) == "📚" and not helpf.hasRole(userID, "student"):
			await helpf.giveRole(userID, "student")
		elif str(payload.emoji) == "👾" and not helpf.hasRole(userID, "dev-tech"):
			await helpf.giveRole(userID, "dev-tech")
		elif str(payload.emoji) == "🏹" and not helpf.hasRole(userID, "single"):
			await helpf.giveRole(userID, "single")
		elif str(payload.emoji) == "🤑" and not helpf.hasRole(userID, "gambling"):
			await helpf.giveRole(userID, "gambling")
		elif str(payload.emoji) == "⚡" and not helpf.hasRole(userID, "bot-dev"):
			await helpf.giveRole(userID, "bot-dev")
		else:
			await message.remove_reaction(payload.emoji, payload.member)

	# When user can not get rolls
	elif state == 6 and not helpf.hasRole(userID, "rookie"):
		await message.remove_reaction(payload.emoji, payload.member)

	# Member is reacting to other members and gets XP
	else:
		#Give reaction XP
		channel = bot.get_channel(payload.channel_id)
		whiteList = jh.config["serverTextWhitelist"]
		if jh.isInWhitelist(payload.channel_id):
			message = await channel.fetch_message(payload.message_id)
			if not (message.author.bot or payload.member.bot) and jh.getFromConfig("log")=="True":
				jh.addReactionXP(payload.user_id, xpf.randomRange(1,5))
				jh.saveData()

# When member removes a reaction
@bot.event
async def on_raw_reaction_remove(payload):
	userID = payload.user_id
	server = bot.get_guild(payload.guild_id)
	member = server.get_member(userID)
	message = await helpf.getMessageFromPayload(payload)
	[state, page] = helpf.getMessageState(message)

	# If member revokes his accetptans of the Note on data processing
	if state == 5 and (helpf.hasRole(userID, "rookie") or helpf.hasRole(userID, "etwasse")):
		await helpf.removeRoles(userID, ["chairman", "associate", "employee", "rookie", "etwasse"])

	# When member revokes his interest in interest groups
	elif state == 6:
		if not helpf.hasRole(userID, "rookie") and not helpf.hasRole(userID, "etwasse"):
			await message.remove_reaction(payload.emoji, member)
		elif str(payload.emoji) == "🎮" and helpf.hasRole(userID, "gaming"):
			await helpf.removeRole(userID, "gaming")
		elif str(payload.emoji) == "📚" and helpf.hasRole(userID, "student"):
			await helpf.removeRole(userID, "student")
		elif str(payload.emoji) == "👾" and helpf.hasRole(userID, "dev-tech"):
			await helpf.removeRole(userID, "dev-tech")
		elif str(payload.emoji) == "🏹" and await .hasRole(userID, "single"):
			await helpf.removeRole(userID, "single")
		elif str(payload.emoji) == "🤑" and await .hasRole(userID, "gambling"):
			await helpf.removeRole(userID, "gambling")
		elif str(payload.emoji) == "⚡" and await .hasRole(userID, "bot-dev"):
			await helpf.removeRole(userID, "bot-dev")
"""
@bot.event
async def on_error(event, *args, **kwargs):
	message = f"\n_________\nERROR:\nEvent:\n\t{event}\n\nPosition:\n\t{args}\n\nKeyword:\n\t{kwargs}\nERROR END\n_________\n"
	await helpf.log(message,2)
"""

jh.config["log"] = "False"
jh.saveConfig()
print("Set log to False.")
print("Loading Commands...")
bot.add_cog(Commanduser(bot, helpf, jh, xpf))
bot.add_cog(Commandmod(bot, helpf, jh, xpf))
bot.add_cog(Commandowner(bot, helpf, tban, jh, xpf))
bot.add_cog(Commandpoll(bot, helpf, poll, jh))
bot.add_cog(Commandmodserver(bot, helpf, tban, cntr, jh))
print("Commands loaded.")

print("Starting Bot...")
bot.run(jh.getFromConfig("token"))