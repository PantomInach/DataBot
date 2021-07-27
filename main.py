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
from bot.constructer import Constructer
from bot.commanduser import Commanduser
from bot.commandmod import Commandmod
from bot.commandowner import Commandowner
from bot.commandpoll import Commandpoll
from bot.commandmodserver import Commandmodserver
from bot.textban import Textban
import asyncio

cons = Constructer()
[jh, xpf, poll, tban, cntr] = cons.giveObjects()
print("Jsonhandel, Xpfunk, Poll and Textban Object created.")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix = jh.getFromConfig("command_prefix"), intents=intents)

print("Constructing helpfunc Object...")
helpf = Helpfunc(bot, jh, xpf)
print("Helpfunc Object created.")

#Sends mesage to owner, when bot is online
@bot.event
async def on_ready():
    print("Now Online")
    owner = bot.get_user(int(jh.getFromConfig("owner")))
    #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{jh.getFromConfig("command_prefix")}help"))
    await helpf.sendModsMessage("Bot ist online")

@bot.event
async def on_message(message):
	if (message.author == bot.user):
		return
	if tban.hasTextBan(int(message.author.id)) and not isinstance(message.channel, discord.channel.DMChannel):
		await message.delete()
		return
	a = ""
	a += message.content
	if str(message.channel.id) == str(jh.getFromConfig("levelchannel")) and a[0] != jh.getFromConfig("command_prefix"):
		await message.delete()
		return
	#Check if picture
	if len(message.attachments) > 0 and jh.getFromConfig("log")=="True":
		attachments = message.attachments
		userID = message.author.id
		for attachment in attachments:
			name = attachment.filename
			if name[-3:] == "jpg" or name[-3:] == "png":
				jh.dataAddText(userID, xpf.randomRange(20,40))
				jh.saveData()
				return
	#When Message ist a String
	if a != "" and a[0] != jh.getFromConfig("command_prefix") and jh.getFromConfig("log")=="True":
		#Give XP
		whiteList = jh.config["serverTextWhitelist"]
		messageid = message.channel.id
		if str(messageid) in set(whiteList):
			userID = message.author.id
			jh.dataAddText(userID, xpf.textXP(a))
			jh.saveData()
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

@bot.event
async def on_member_join(member):
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	server = bot.get_guild(int(jh.getFromConfig("server")))
	await channel.send(f"Hey **{member.name}**, welcome to {server}")

@bot.event
async def on_member_remove(member):
	channel = bot.get_channel(int(jh.getFromConfig("logchannel")))
	server = bot.get_guild(int(jh.getFromConfig("server")))
	await channel.send(f"**{member.name}** has left {server}. Press F to pay respect.")
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

@bot.event
async def on_raw_reaction_add(payload):
	if bot.get_user(payload.user_id).bot:
		return
	userID = payload.user_id
	message = await helpf.getMessageFromPayload(payload)
	[state, page] = await helpf.getMessageState(message)
	#normal message when (0,x)
	#Stage [1,3] =^= message is Leaderboard
	if state in range(1,4):
		#Handel Leaderboard reactions
		change = await helpf.messageToState(message)
		await message.clear_reactions()
		if state >= 6:
			return
		if change <3:
			choice = [0, page-1 if page-1>=0 else 0, page+1]  
			page = choice[change]
		else:
			state = change-2
		text = await helpf.getLeaderboardXBy(page, state)
		if text == "":
			page -= 1
			text = await helpf.getLeaderboardXBy(page, state)
		await message.edit(content=f"{text}{payload.member.mention}")
		reactionsarr = ["⏫","⬅","➡","⏰","💌","🌟"]
		removeemoji = [5,3,4]
		del reactionsarr[removeemoji[state-1]]
		for emoji in reactionsarr:
			await message.add_reaction(emoji)
		return
	#State 4 =^= message is poll
	elif state == 4:
		newVote = await helpf.voteOption(message)
		if await helpf.hasRole(userID, "employee"):
			pollID = int(str(message.content)[6:10])
			optionName = poll.getOptionByNumber(pollID, newVote+1)
			poll.addUserVote(pollID, userID, optionName)
			await message.edit(content=f"{poll.pollString(pollID)}")
		await message.clear_reactions()
		reactionsarr = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣","6⃣","7⃣"]
		for i in range(len(poll.getOptions(pollID))):
			await message.add_reaction(reactionsarr[i])
	elif state == 5:
		if not await helpf.hasRole(userID, "rookie"):
			await helpf.giveRole(userID, "rookie")
	elif state == 6 and (await helpf.hasRole(userID, "rookie") or await helpf.hasRole(userID, "etwasse")):
		if str(payload.emoji) == "🎮" and not await helpf.hasRole(userID, "gaming"):
			await helpf.giveRole(userID, "gaming")
		elif str(payload.emoji) == "📚" and not await helpf.hasRole(userID, "student"):
			await helpf.giveRole(userID, "student")
		elif str(payload.emoji) == "👾" and not await helpf.hasRole(userID, "dev-tech"):
			await helpf.giveRole(userID, "dev-tech")
		elif str(payload.emoji) == "🏹" and not await helpf.hasRole(userID, "single"):
			await helpf.giveRole(userID, "single")
		elif str(payload.emoji) == "🤑" and not await helpf.hasRole(userID, "gambling"):
			await helpf.giveRole(userID, "gambling")
		elif str(payload.emoji) == "⚡" and not await helpf.hasRole(userID, "bot-dev"):
			await helpf.giveRole(userID, "bot-dev")
		else:
			await message.remove_reaction(payload.emoji, payload.member)
	elif state == 6 and not await helpf.hasRole(userID, "rookie"):
		await message.remove_reaction(payload.emoji, payload.member)
	else:
		#Give reaction XP
		channel = bot.get_channel(payload.channel_id)
		whiteList = jh.config["serverTextWhitelist"]
		if str(payload.channel_id) in set(whiteList):
			message = await channel.fetch_message(payload.message_id)
			if not (message.author.bot or payload.member.bot) and jh.getFromConfig("log")=="True":
				jh.dataAddReaction(payload.user_id, xpf.randomRange(1,5))
				jh.saveData()
		return

@bot.event
async def on_raw_reaction_remove(payload):
	userID = payload.user_id
	server = bot.get_guild(payload.guild_id)
	member = server.get_member(userID)
	message = await helpf.getMessageFromPayload(payload)
	[state, page] = await helpf.getMessageState(message)
	if state == 5 and (await helpf.hasRole(userID, "rookie") or await helpf.hasRole(userID, "etwasse")):
		await helpf.removeRoles(userID, ["chairman", "associate", "employee", "rookie", "etwasse"])
	if state == 6:
		if not await helpf.hasRole(userID, "rookie") and not await helpf.hasRole(userID, "etwasse"):
			await message.remove_reaction(payload.emoji, member)
		elif str(payload.emoji) == "🎮" and await helpf.hasRole(userID, "gaming"):
			await helpf.removeRole(userID, "gaming")
		elif str(payload.emoji) == "📚" and await helpf.hasRole(userID, "student"):
			await helpf.removeRole(userID, "student")
		elif str(payload.emoji) == "👾" and await helpf.hasRole(userID, "dev-tech"):
			await helpf.removeRole(userID, "dev-tech")
		elif str(payload.emoji) == "🏹" and await helpf.hasRole(userID, "single"):
			await helpf.removeRole(userID, "single")
		elif str(payload.emoji) == "🤑" and await helpf.hasRole(userID, "gambling"):
			await helpf.removeRole(userID, "gambling")
		elif str(payload.emoji) == "⚡" and await helpf.hasRole(userID, "bot-dev"):
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