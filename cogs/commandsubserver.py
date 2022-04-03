import discord
from discord.ext import commands
import asyncio

from discord.utils import find

from helpfunctions.decorators import isDMCommand, isBotOwnerCommand
from helpfunctions.utils import Utils
from datahandler.jsonhandel import Jsonhandel

from hashlib import sha512

def hasAnyRole(*items):
	"""
	Type:	Decorator of @commands.command Bot functions.

	param items:	Tuple of Strings and/or integers wit Discord Channel IDs or names.

	Check if a user has any of the roles in items.

	Only use for commands, which USE @commands.command
	commands.has_any_role() does not work in DM since a users can't have roles.
	This one pulls the roles from the configured guild and makes the same check as commands.has_any_role().

	Function is not in decorators.py since the Helpfunction Object is needed.
	"""
	def predicate(ctx):
		return Commandsubserver.utils.hasOneRole(ctx.author.id, [*items])
	return commands.check(predicate)

def hasSubserverRoles():
	"""
	Type:	Decorator for functions with self in args[0] and ctx object in args[1].

	param items:	Tuple of Strings and/or integers wit Discord Channel IDs or names.

	Check if a user has all of the roles in items.

	Only use for commands, which USE @commands.command
	commands.has_any_role() does not work in DM since a users can't have roles.
	This one pulls the roles from the configured guild and makes the same check as commands.has_any_role().

	Function is not in decorators.py since the Helpfunction Object is needed.
	"""
	def predicate(ctx):
		return Commandsubserver.utils.hasRoles(ctx.author.id, Commandsubserver.subserver_role)
	return commands.check(predicate)

class Commandsubserver(commands.Cog, name='Subserver Commands'):
	"""
	Group of sub server commands.

	These commands are for creating, joining, leaving and manage sub server.

	Subservers are hidden parts of a server, which only members of a subserver can see.
	This keeps the guild smaller and clearer.

	Every subserver consists of at least 3 channels.
	One voice channel is to switch to the subserver by joining it. It had been successful if you were disconnected from the channel.
	The other two channels are the subserver. Optionally there can be more.


	List of subservers:
		To get an overview of all subservers use the command 'sub list'.
	Creating a subserver:
		A subserver can be created by a member with the 'COO' role with the command 'sub create [name]'.
		There will be 2 voice and 1 text channel created.
		Also it is recommended, that you create a invite code via 'sub inv create {[sub id]/[sub_name]}'.	
	Joining a subserver:
		With an invite code you can join the subserver with the command 'sub join [sub_inv_code]'.
		Also if someone on the subserver can invite someone else with 'sub invite {[user'id]/[user name]} {[subID]/[sub_name]}'.
	Leaving a subserver:
		If you don't want to be part of the subserver anymore, you can leave it permanently with 'sub leave {[sub id]/[sub_name]}'.
	Switching subserver:
		You can switch to another subserver with the command 'sub way {[subID]/[sub_name]} ' if you are already member of it.
		Also you can join the gateway channel to do so. This had been successful if you were disconnected from this voice channel.
		To switch to the main server again use 'sub stop'.
	Removing a subserver:
		To irrevocable remove a sub server use 'sub rm {[subID/[sub_name]}'. Can only be done by users with at least the role 'COO'.	
	"""

	def __init__(self, bot):
		super(Commandsubserver, self).__init__()
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		Commandsubserver.utils = self.utils
		Commandsubserver.subserver_role = self.jh.get_subserver_needed_roles()

	@commands.group(name = 'sub', brief = 'Group of subserver commands.')
	@hasSubserverRoles()
	async def sub(self, ctx):
		"""
		Group of subserver commands.

		Commands:
			Listing subserver:		sub list
			Create subserver:		sub create [sub_name]
			Create subserver invite:	sub invite create [sub_name]
			Inviting member:		sub inv [userID] [sub_name]
			Joining subserver:		sub join [sub_inv_code]
			Leaving subserver:		sub leave [sub_name]
			Switch subserver:		sub way [sub_name]
			Return to Main server:		sub stop
			Delete subserver:		sub rm [sub_name]

		More info can be found via 'help sub [command]'.

		All commands in the list below can be executed in this channel.
		"""
		"""
		param ctx:	Discord Context object. Automatically passed.

		Is the parent command for the 'sub' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: list, create, invite, rm, inv, join, leave, sw, ss", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help sub' or '+help Subserver Commands'")
			await ctx.send(embed = embed, delete_after = 3600)

	@sub.command(name = 'create', brief = 'Creates a subserver.')
	@isDMCommand()
	@hasAnyRole("CEO","COO")
	async def create(self, ctx, subserver_name):
		"""
		To create a subserver use the command 'sub create [subserver name]'.
		The subserver_name will be converted to lower case and the spaces will be removed.
		When the name is longer than 16 letters, an error will be thrown.
		If the name is already taken, you get an error message.
		If the gateway category is not created yet, this command will do it.

		There will be a new gateway channel with the given name and a new category with a text channel and an expanding voice channel.

		Can only be used in the bot-DM and only by members with one of the roles 'CEO' or 'COO'.
		"""
		"""
		param ctx:	Discord Context object. Automatically passed.
		param subserver_name:	String. Will be sterilize the input by removing spaces and converting it to lower case. Needs sterilized a max length of 16.

		Generates the two needed subserver roles first.
		Then creates the category for the subserver and fills it with its two channels.
		If there isn't already a gateway category, one will be created.
		Finally the gateway channel for the subserver will be created.

		All channel have the required permissions.

		If the subserver name is already taken, an error message will be sent.
		"""
		subserver_name = subserver_name.lower().replace(" ","")
		if len(subserver_name) > 16:
			await ctx.send(f"ERROR: Subserver name must have 16 or less characters. The given name {subserver_name} has {len(subserver_name)}.")
			return

		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))

		# Test if subserver already exists
		if "sub-" + subserver_name in guild.roles:
			await ctx.send(f"There already exists a subserver with the name {subserver_name}.", delete_after = 3600)
			return

		# Create subserver roles
		sub_way_role = await guild.create_role(name = 'sw-' + subserver_name, color = 13277615, reason = 'Creating new subserver')
		sub_role = await guild.create_role(name = 'sub-' + subserver_name, color = 13277615, reason = 'Creating new subserver')
		# Creates subserver  category
		sub_category = await guild.create_category(name = 'sub-' + subserver_name, overwrites = {
				guild.me: discord.PermissionOverwrite(manage_channels = True, view_channel = True),
				sub_role: discord.PermissionOverwrite(read_messages = True, connect = True, view_channel = True),
				guild.default_role: discord.PermissionOverwrite(read_messages = False, connect = False, view_channel = False)				
			})

		# Creates subserver channel
		sub_channel = await guild.create_text_channel(name = 'text-' + subserver_name, category = sub_category)
		sub_voice_channel = await guild.create_voice_channel(name = subserver_name + " #1", category = sub_category, overwrites = {
				guild.me: discord.PermissionOverwrite(manage_channels = True, view_channel = True),
				guild.default_role: discord.PermissionOverwrite(view_channel = False),
				sub_role: discord.PermissionOverwrite(view_channel = True)
			})

		sub_way_category = find(lambda c: c.name == 'Subserver Gateway', guild.categories)
		# If no subway category is available, create one
		if not sub_way_category:
			sub_way_category = await guild.create_category(name = 'Subserver Gateway', overwrites = {
					guild.me: discord.PermissionOverwrite(manage_channels = True, view_channel = True),
					guild.default_role: discord.PermissionOverwrite()
				})

		# Create gateway channel
		await guild.create_voice_channel(name = subserver_name + " (0/0/0)", category = sub_way_category, overwrites = {
				guild.me: discord.PermissionOverwrite(manage_channels = True, view_channel = True),
				sub_way_role: discord.PermissionOverwrite(connect = True, view_channel = True),
				guild.default_role: discord.PermissionOverwrite(connect = False, view_channel = False)		
			})

		# Give bot the sub-roles. Needed to delete them. Don't ask me why it needs them.
		await guild.me.add_roles(sub_way_role, sub_role)

	@sub.command(name = 'rm', brief = 'Removes a subserver.')
	@isDMCommand()
	@hasAnyRole("COO", "CEO")
	async def remove(self, ctx, name):
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		sub_category = self.get_subserver_category_by_name(name)
		sub_way_category = find(lambda c: c.name == 'Subserver Gateway', guild.categories)
		sub_way_channel = find(lambda ch: ch.name.startswith(name), sub_way_category.voice_channels)
		if not (sub_category or sub_way_channel):
			await ctx.send(f"ERROR: No subserver with name {name} found.", delete_after = 3600)
			return
		if sub_category:
			for ch in sub_category.channels:
				await ch.delete()
			await sub_category.delete()

		if sub_way_channel:
			await sub_way_channel.delete()
		else:
			await ctx.send(f"WARNING: No subway channel found.", delete_after = 3600)

		for role in self.get_subserver_roles(name):
			if role:
				await role.delete()
			else:
				await ctx.send(f"WARNING: No subway role found.", delete_after = 3600)

	@sub.command(name = 'list', brief = 'List all subserver.')
	@isDMCommand()
	async def list(self, ctx):
		"""
		With the command 'sub list' you get an overview of all subserver, how many people are in the voice channel, how many people are currently in the subserver and how many members the subserver has.

		This command can only be used in the DM.
		"""
		"""
		Sends an embeded back containing all subserver, how many people are in the voice channel, how many people are currently in the subserver and how many members the subserver has.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		embed = discord.Embed(title = "Subserver List", 
									description = "(User connected / User online / User total)", 
									color = 12008408)
		embed.set_thumbnail(url = guild.icon_url)
		info_dict = self.get_subserver_user_amount_info()
		for subserver_name in info_dict.keys():
			(user_connected, user_online, user_total) = info_dict[subserver_name]
			embed.add_field(name = subserver_name, value = f"({user_connected}/{user_online}/{user_total})", inline=True)
		await ctx.send(embed=embed)

	@sub.group(name = 'inv', brief = 'Invite a member to a subserver.')
	@isDMCommand()
	async def inv(self, ctx, userID, subserver_name):
		"""
		With the command 'sub inv [user ID] [suberver name]' an other member can be invited to the subserver.
		Only a member of a subserver can invite another one.

		This command can only be used in the DM.
		"""
		"""
		param userID:	Integer of userID
		param subserver_name: String

		Gives the member with the userID the sub_way role of the subserver if all inputs are correct and author is a member of the subserver.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		(sub_role, sub_way_role) = self.get_subserver_roles(subserver_name)
		# Check if subserver exists
		if not (sub_role and sub_way_role):
			await ctx.send(f"ERROR! Subserver with name {subserver_name} not found.", delete_after = 3600)
			return
		# Author is not in subserver
		author_member = guild.get_member(ctx.author.id)
		if not author_member in sub_way_role.members:
			await ctx.send(f"ERROR! You can not invite users to a subserver, you aren't a member of.", delete_after = 3600)
			return
		# Check for valid user ID
		if not userID.isdigit():
			await ctx.send(f"ERROR! User ID must be a number.", delete_after = 3600)
			return
		# Search for member to be invited
		to_invite = guild.get_member(int(userID))
		if not to_invite:
			await ctx.send(f"ERROR! Could not find user with ID {userID}.", delete_after = 3600)
			return
		if to_invite in sub_way_role.members:
			await ctx.send(f"ERROR! User {to_invite.name} is already a member of {subserver_name}.", delete_after = 3600)
			return
		await to_invite.add_roles(sub_way_role)
		await self.update_subserver_info()

	@sub.command(name = 'leave', brief = 'Leave a subserver permanently.')
	@isDMCommand()
	async def leave(self, ctx, subserver_name):
		"""
		If you want to leave a subserver permanently, then use the command 'sub leave [subserver name]'.
		!!! WARNING !!! Action can not be reversed by yourself. Someone else must invite you or you have to use an invite code.

		This command can only be used in the DM.
		"""
		"""
		param subserver_name: String

		Removes member from subserver by removing subserver_roles.
		"""
		(sub_role, sub_way_role) = self.get_subserver_roles(subserver_name)
		# Check if subserver exists
		if not (sub_role and sub_way_role):
			await ctx.send(f"ERROR! Subserver with name {subserver_name} not found.", delete_after = 3600)
			return
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		author_member = guild.get_member(ctx.author.id)
		if author_member in sub_role.members:
			await author_member.remove_roles(sub_role, reason = f"Member {ctx.author.name} decided to leave the subserver {subserver_name}.")
		if author_member in sub_way_role.members:
			await author_member.remove_roles(sub_way_role, reason = f"Member {ctx.author.name} decided to leave the subserver {subserver_name}.")
		await ctx.send(f"You left subserver {subserver_name}.", delete_after = 60)
		await self.update_subserver_info()

	@sub.command(name = 'stop', brief = 'Leave a subserver NOT permanently.')
	@isDMCommand()
	async def substop(self, ctx):
		"""
		To leave your current subserver and return to the main server use 'sub stop'.

		This command can only be used in the DM.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		author_member = guild.get_member(ctx.author.id)
		if await self.leave_current_subserver_no_permanent(author_member):
			await ctx.send("You left your current subserver.", delete_after = 60)
			await self.update_subserver_info()
		else:
			await ctx.send("Your are not on the guild.", delete_after = 60)

	@sub.command(name = 'way', brief = 'Change subserver.')
	@isDMCommand()
	async def subway(self, ctx, subserver_name):
		"""
		Use 'sub way [sub_name]' to enter a subserver, which you have joined.
		When you already joined a subserver, you will switch to the new one.
		Has the same effect as joining a subway channel.

		This command can only be used in the DM.
		"""
		"""
		param subserver_name:	String

		Removes sub-roles and gives sub-role from subersever-name 
		"""
		(sub_role, sub_way_role) = self.get_subserver_roles(subserver_name)
		if not (sub_role and sub_way_role):
			await ctx.send(f"ERROR! No subserver with name {subserver_name}.")
			return
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		author_member = guild.get_member(ctx.author.id)
		if not author_member:
			await ctx.send("ERROR! Your are not on the guild.")
			return
		if not sub_way_role in author_member.roles:
			await ctx.send("ERROR! Your are not on the subserver.")
			return
		if await self.change_subserver(author_member, to = subserver_name):
			await ctx.send(f"You made your way to the subserver {subserver_name}", delete_after = 60)
			await self.update_subserver_info()
		else:
			await ctx.send("Your are not on the guild.", delete_after = 60)

	@sub.group(name = 'invite', brief = "Group of invite commands.")
	@isDMCommand()
	async def invite(self, ctx):
		"""
		Group of subserver invite commands.

		Commands:
			Create subserver invite:	sub invite create [sub_name]

		More info can be found via 'help sub [command]'.

		All commands in the list below can be executed in this channel.
		"""
		if ctx.invoked_subcommand is None:
			embed=discord.Embed(title = "You need to specify a subcommand. Possible subcommands: create", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help sub invite' or '+help Subserver Commands'")
			await ctx.send(embed = embed, delete_after = 3600)

	@invite.command(name = 'create', brief = 'Creates a invite code.')
	@isDMCommand()
	@hasAnyRole("CEO", "COO")
	async def create_code(self, ctx, subserver_name):
		"""
		Creates an invite code for a subserver with the command 'sub invite create [subserver name]'.
		
		This command can only be used in the DM.
		"""
		"""
		param subserver_name:	String

		Creates an invite code with the function hash_invite_code and sends it to the user.
		"""
		(sub_role, sub_way_role) = self.get_subserver_roles(subserver_name)
		if not (sub_role and sub_way_role):
			await ctx.send(f"ERROR! No subserver with name {subserver_name}.")
			return
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		code = self.hash_invite_code(subserver_name)
		embed=discord.Embed(title = f"Invite Code for subserver {subserver_name}", description = code, color = 12008408)
		embed.set_footer(text = f"Use command 'sub join {code}' to join subserver.")
		embed.set_thumbnail(url = guild.icon_url)
		await ctx.send(embed = embed)

	@sub.command(name = 'join', brief = 'Join a subserver with code.')
	@isDMCommand()
	async def join(self, ctx, code):
		"""
		To join a subserver with an invite code use the command 'sub join [code]'.

		This command can only be used in the DM.
		"""
		"""
		param code: String

		Computes all hashes of a subserver till the right subserver is hit. Then gives the member the corresponding subserver role.
		If none is found, than print error message.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		subserver = self.get_all_subserver_roles()
		all_suberver_names = [sub.name.split("-")[1] for sub, _ in subserver]
		# Search for matching hash
		i = 0
		hashed_code = self.hash_invite_code(all_suberver_names[i])
		while i < len(all_suberver_names) - 1 and hashed_code != code:
			i += 1
			hashed_code = self.hash_invite_code(all_suberver_names[i])
		# Check if search was successful.
		author_member = guild.get_member(ctx.author.id)
		if i >= len(all_suberver_names) - 1 or not author_member:
			await asyncio.sleep(1)
			await ctx.send(f"ERROR! Code does not match any invite code of any subserver.")
			return
		if not author_member in subserver[i][1].members:
			await author_member.add_roles(subserver[i][1])
		await ctx.send(f"You joined the subserver **{all_suberver_names[i]}**.")
		await self.update_subserver_info()

	"""
	######################################################################

	Subserver commands end

	######################################################################
	"""

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		"""
		Handles the subserver gateway functions
		When a member connects to a subway channel, he will get the corresponding role.
		"""
		# Subway channel function
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		category = find(lambda c: after.channel in c.channels, guild.categories)
		# Switch to subserver
		if category and category.name == "Subserver Gateway" and after.channel and after.channel in category.voice_channels:
			# Get Subserver_name. 
			subserver_name = self.get_subserver_name_from_channel(after.channel.name)
			await self.change_subserver(member, to = subserver_name)
			await member.move_to(None)
			await self.update_subserver_info()

	def get_subserver_roles(self, sub_name):
		"""
		param sub_name:	String

		Finds the sub and subway roles of the subserver with the name sub_name.

		Returns the roles. When none is found, the return for the roles is None.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		sub_role = find(lambda r: r.name == "sub-" + sub_name, guild.roles)
		sub_way_role = find(lambda r: r.name == "sw-" + sub_name, guild.roles)
		return (sub_role, sub_way_role)

	def get_all_subserver_roles(self):
		"""
		Returns a list of tuple of roles, which contain the subserver and subway role.
		Note that a subserver name is in the return when the role "sub-..." exists.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		sub_roles = [role for role in guild.roles if role.name.startswith("sub-") or role.name.startswith("sw-")]
		# Sort by subserver name. '+ r.name[1]' is for sorting sub roles on top of subway roles, since '+ r.name[1]' is 'u' or 'w'.
		sorted_roles = sorted(sub_roles, key = lambda r: r.name.split("-")[1] + r.name[1])
		if not sorted_roles:
			return []
		# Data pattern: [(sub-a, sw-a), ...]
		re =  [(sorted_roles[i], sorted_roles[i + 1]) for i in range(0, len(sorted_roles), 2)]
		return re

	def get_subserver_users_per_role(self):
		"""
		Gets the amount of users in the subserver and the amount of users currently using the subserver.
		This is done by looking up how many people have the role "sub-..." and "sw-...".

		Returns a dict with the key subserver roles with a tuple of to integers.
		"""
		out = {}
		for role in self.get_all_subserver_roles():
			out[role[0]] = (len(role[0].members), len(role[1].members)) 
		return out

	def get_subserver_category_by_name(self, name):
		"""
		param name:	String.

		Searches the subserver category for the matching name and returns it.
		Otherwise return None.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		for cat in guild.categories:
			if cat.name == "sub-" + name:
				return cat
		return None

	async def change_subserver(self, member, to = None):
		"""
		param member:	Discord Member object
		param to:	To which subserver. None => Leave subserver

		Removes member from current subserver and lets him join new subserver defined to.
		Returns True if operation was successful.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		if not member:
			return False
		succesful = await self.leave_current_subserver_no_permanent(member)
		if not succesful:
			return False
		if to:
			(sub_role, sub_way_role) = self.get_subserver_roles(to)
			if sub_role and sub_way_role:
				await member.add_roles(sub_role, reason = f"Member {member.name} switched subserver.")
		return True

	async def leave_current_subserver_no_permanent(self, member):
		"""
		param member: Discord Member object

		Removes all sub-roles of user.
		Returns True if operation was successful.
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		if not member:
			return False
		sub_roles = [role for role in member.roles if role.name.startswith("sub-")]
		if sub_roles:
			await member.remove_roles(*sub_roles)
		return True

	def get_subserver_user_amount_info(self):
		"""
		Gets the amount of connected users, online users and total users in the subserver for each subserver.
		Returns a dict with the subserver_name as key and the data as a triple.
		Exp.: {"test": (0,2,4), "test2": (3,6,8), ...}  
		"""
		info_dict = {}
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		subserver_dict = self.get_subserver_users_per_role()
		for key in subserver_dict.keys():
			subserver_name = key.name[4:]
			sub_cat = self.get_subserver_category_by_name(subserver_name)
			# Get connected user
			user_connected = 0
			if sub_cat:
				for vc in sub_cat.voice_channels:
					user_connected += len(vc.members)
			user_online = subserver_dict[key][0] - 1 # -1 for bot
			user_total = subserver_dict[key][1] - 1
			# Insert info into dict
			info_dict[subserver_name] = (user_connected, user_online, user_total)
		return info_dict

	async def update_subserver_info(self):
		"""
		Updates the member info for each channel in the subway gateway if necessary
		"""
		guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
		category = find(lambda cat: cat.name == "Subserver Gateway", guild.categories)
		info_dict = self.get_subserver_user_amount_info()
		subservers = [channel for channel in category.voice_channels]
		for subserver in subservers:
			subserver_name = self.get_subserver_name_from_channel(subserver.name)
			current_info = self.get_subserver_info_from_subserver_name(subserver.name)
			if not current_info:
				# Error when no current info is available
				# TODO: Make bot fix naming itself
				await self.utils.sendModsMessage(f"WARNING! Subserver {subserver_name} has an invalid name. Updating of subserver gateway be suppressed for some subservers. Please bring the name into its correct format of \"[subserver_name] (0/0/0)\".")
				return
			new_info = info_dict[subserver_name]
			if new_info != current_info:
				await subserver.edit(name = subserver_name + " " + str(new_info).replace(", ", "/"))

	def get_subserver_info_from_subserver_name(self, subserver_name):
		"""
		param subserver_name:	String

		Extracts subserver gateway channel name member infos from its name.
		Returns tuple with user_connected, user_connected, user_total
		"""
		info_string = subserver_name.split("(")[-1][:-1].split("/")
		if [s for s in info_string if not s.isdigit()]:
			return None
		return tuple([int(string) for string in info_string])

	def get_subserver_name_from_channel(self, channel_name):
		"""
		param channel:	Discord Channel object

		Returns subserver_name from channel.
		Exp.: channel.name = "test(13 (34/254/278)" => "test(13"
		"""
		return "(".join(channel_name.split("(")[:-1]).replace(" ","")

	def hash_invite_code(self, subserver_name):
		token = self.jh.get_token()
		code = sha512((token[::2] + subserver_name).encode()).hexdigest()
		token = ""
		return code[:8]

def setup(bot):
	bot.add_cog(Commandsubserver(bot))
