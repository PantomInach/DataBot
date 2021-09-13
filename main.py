import certifi
import os
import discord
from discord.utils import get, find
from discord.ext import commands
import time
import datetime
import asyncio

from bot.jsonhandel import Jsonhandel
from bot.xpfunk import Xpfunk
from bot.poll import Poll
from bot.helpfunc import Helpfunc
from bot.textban import Textban
from bot.counter import Counter

from bot.commanduser import Commanduser
from bot.commandmod import Commandmod
from bot.commandowner import Commandowner
from bot.commandpoll import Commandpoll
from bot.commandmodserver import Commandmodserver
from bot.subroutine import Sub

print("[Startup] Prepare to start Bot...")

# Create Objects for passing to command classes
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
# Create subroutine object
sub = Sub(helpf)

print("[Startup] Objects created")



"""
In the following code there will be the bot.events defined.
Bot events are called when a specific action is seen by the bot. 
"""



# When bot is connected
@bot.event
async def on_ready():
	#Sends mesage to mods, when bot is online
    print("Now Online")
    await helpf.sendModsMessage(f"Bot is now online.\nVersion:\tWorkingDiscordBot v1.1.1-beta")

    # Tries to start the subroutine. When it is running, than nothing will happen.
    sub.startSubRoutine()

# When bot reads a message
@bot.event
async def on_message(message):
	"""
	param message:	Message read by the bot

	Ignore bot messages
	"""
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
		if jh.isInWhitelist(message.channel.id):
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
	"""
	param member:	User on guilde

	Creates a welcom message in the logchannel
	"""
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	guilde = bot.get_guild(int(jh.getFromConfig("guilde")))
	await channel.send(f"Hey **{member.name}**, welcome to {guilde}")


# When a member leaves the guilde
@bot.event
async def on_member_remove(member):
	"""
	param member:	User on guilde

	Sends a goodbye message in the logchannel
	"""
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	guilde = bot.get_guild(int(jh.getFromConfig("guilde")))
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
	"""
	param payload:	Gives context about the added reaction

	Handels diffrent bot interactions with the server via ractions.

	First:
		Handles leaderboard interactions for new page and new sorting.
	Second:
		Handels voting on polls.
	Third:
		Give role on data processing.
	Forth:
		Handels ractions on interest groups for user the get rolees.
	Fifth:
		Give XP when a reaction is added.
	"""


	# Ignore bot reactions
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
	
	# Stage [1,3] =^= message is Leaderboard
	if state in range(1,4):
		# Handel Leaderboard reactions
		change = helpf.getLeaderboardChange(message)
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
		sortBy = state - 1
		"""
		sortBy:
			0 => Sort by voice + text = xp
			1 => Sort by voice
			2 => Sort by textcount
		"""
		if change < 3:
			# Change page if needed
			choice = [0, page-1 if page-1>=0 else 0, page+1]
			page = choice[change]
			# Whip member reaction
			await message.remove_reaction(payload.emoji, payload.member)
		else:
			# Changes the ordering of the leaderboard
			sortBy = change - 3
			"""
			sortBy:
				0 => Sort by voice + text = xp
				1 => Sort by voice
				2 => Sort by textcount
			"""
			# Whip all reactions
			await message.clear_reactions()

		text = helpf.getLeaderboardPageBy(page, sortBy)
		if text == "":
			# If no one is on this page, get last page.
			text = helpf.getLeaderboardPageBy(page - 1, sortBy)

		# Changes Leaderboard and adds reactions	
		await message.edit(content=f"{text}{payload.member.mention}")
		if change >= 3:
			# When all reactions were whippe. Added new Reactions
			reactionsarr = ["⏫","⬅","➡","⏰","💌","🌟"]
			removeemoji = [5,3,4]
			del reactionsarr[removeemoji[sortBy]]
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
		# Give role for using server
		if not helpf.hasRole(userID, "rookie"):
			await helpf.giveRole(userID, "rookie")

	# State 6 =^= User interest groups
	elif state == 6 and (helpf.hasRole(userID, "rookie") or helpf.hasRole(userID, "etwasse")):
		# User needs to accept Note on data processing before using this feature
		# Gives user role depending on what they react on
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

	# When user can not get roles
	elif state == 6 and not helpf.hasRole(userID, "rookie"):
		# Removes user reaction
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
	"""
	param payload:	Gives context about the removed reaction

	Handels user interaction in which reactions are removed.

	First:
		Note on data processing remove server role
	Second:
		Remove user roles on interset groups when a raction is removed 
	"""
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

		elif str(payload.emoji) == "🏹" and helpf.hasRole(userID, "single"):
			await helpf.removeRole(userID, "single")

		elif str(payload.emoji) == "🤑" and helpf.hasRole(userID, "gambling"):
			await helpf.removeRole(userID, "gambling")

		elif str(payload.emoji) == "⚡" and helpf.hasRole(userID, "bot-dev"):
			await helpf.removeRole(userID, "bot-dev")
"""
@bot.event
async def on_error(event, *args, **kwargs):
	message = f"\n_________\nERROR:\nEvent:\n\t{event}\n\nPosition:\n\t{args}\n\nKeyword:\n\t{kwargs}\nERROR END\n_________\n"
	await helpf.log(message,2)
"""

# When a user changes his voice state
@bot.event
async def on_voice_state_update(member, before, after):
	"""
	Handels user interactions when a user changes his voice stage.
	A voice change is when a member changes/joins a channel, mutes/unmutes himself, deafs/undeafs himself.

	param member:	User on guilde
	param before:	Gives the voice state before the change
	param after:	Gives the voice state after the change 

	First:
		Handels voice channel deletion when a user leaves a voice channel and noone else is connected to it.
	Second:
		Creats a new voice channel when all other channels with numbers in the end of its name are occupied.     
	"""
	# when user joins channel: before = None; after is a voicestate


	"""
	When a user leaves a channel (before.channel) with a number endingn nobody else is connected und and number is not 1, than the channel will be deleted.
	"""
	if before.channel and len(before.channel.members) == 0 and before.channel.name[-1].isdigit():
		# Member left first channel
		if before.channel.name[-1] == "1" and not before.channel.name[-2].isdigit():
			# Delete last channel, which has no user in it
			serverid = int(jh.getFromConfig("guilde"))
			allChannel = helpf.getVoiceChannelsFrom(serverid)

			channelWithoutNumber = before.channel.name[:-1]
			notFirstVoiceChannel = [channel for channel in allChannel if channelWithoutNumber in channel.name and len(channel.members) == 0 and channel.name != channelWithoutNumber + "1"]
			if notFirstVoiceChannel:
				lastChannel = max(notFirstVoiceChannel, key = lambda c: int(c.name[len(channelWithoutNumber):]))

				# Removes channel from blacklist if nessacary
				jh.removeFromBalcklist(lastChannel.id)

				await lastChannel.delete()


		# User left channel, which is not the first channel. So it will be deleted	
		else:
			# Removes channel from blacklist if nessacary
			jh.removeFromBalcklist(before.channel.id)
			await before.channel.delete()


	"""
	User joins channel after.channel. If channel ends with a number, than a copy will be created with the lowest possible ending number. 
	"""
	if after.channel and before.channel != after.channel and len(after.channel.members) <= 1:
		# Get channels to get lowest enumeration of channel
		afterNumber = None 
		nameIndex = -1
		while after.channel.name[nameIndex:].isdigit():
			afterNumber = int(after.channel.name[nameIndex:])	# number on the end of channel name
			nameIndex -= 1
		nameIndex += 1

		serverid = int(jh.getFromConfig("guilde"))
		allChannel = helpf.getVoiceChannelsFrom(serverid)
		channelWithoutNumber = after.channel.name[:nameIndex]
		# When after channel name ends with number and channel number 1 has user in it
		if afterNumber and len(find(lambda c: c.name == (channelWithoutNumber + "1"), allChannel).members):
			# Get channels with after.channel.name without numbers in it and end with digits
			voiceChanelsWithName = [channel for channel in allChannel if after.channel.name[:nameIndex] in channel.name and channel.name[len(channelWithoutNumber):].isdigit()]
			# Get all numbers in the end of voiceChannelsWithName
			numbersOfChannels = [int(channel.name[len(channelWithoutNumber):]) for channel in voiceChanelsWithName]
			lowestFreeID = min([i for i in range(2, max(numbersOfChannels) + 2) if not i in numbersOfChannels])
			
			channelWithNumberBefore = find(lambda c: c.name[-len(str(lowestFreeID - 1)):] == str(lowestFreeID - 1), voiceChanelsWithName)
			newChannelName = channelWithoutNumber + str(lowestFreeID)
			# Create channel and gets it
			newChannel = await channelWithNumberBefore.clone(name = newChannelName)

			if jh.isInBlacklist(after.channel.id):
				jh.writeToBalcklist(newChannel.id)

			# Move channel after channelWithNumberBefore
			await newChannel.move(after = channelWithNumberBefore)


jh.config["log"] = "False"
jh.saveConfig()
print("[Startup] Set log to False.")
print("[Startup] Loading Commands...")
bot.add_cog(Commanduser(bot, helpf, tban, jh, xpf, sub))
bot.add_cog(Commandmod(bot, helpf, jh, xpf))
bot.add_cog(Commandowner(bot, helpf, tban, jh, xpf, sub))
bot.add_cog(Commandpoll(bot, helpf, poll, jh))
bot.add_cog(Commandmodserver(bot, helpf, tban, cntr, jh))
print("[Startup] Commands loaded.")

print("[Startup] Starting Bot...")
bot.run(jh.getFromConfig("token"))