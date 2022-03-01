import discord
from discord.ext import commands
from discord.utils import find

import os
import json
from emoji import UNICODE_EMOJI

from helpfunctions.decorators import isBotOwnerCommand, isBotModCommand, isDMCommand, isNotInChannelOrDMCommand
from helpfunctions.utils import Utils
from datahandler.jsonhandel import Jsonhandel

class Commandgiverole(commands.Cog):
	"""
	Manages tables where user can get roles.

	Via a table, a member can get multiple roles via reacting to an emoji on a table.
	When removing a reaction, specified roles will be removed from the member. 

	Config:
		Each 'giverole'- table is a separate json in giveroles.
		JSON:
			{
				"text": "Text from table",
				"channelid": channelid of message,
				"messageid": messageid of table,
				"reactions":{
					"Emoji":([Roles, to, give], [Roles, to, remove]),
					"Emoji2":([Roles, to, give], [Roles, to, remove])
				}
			} 
		The roles can be the name, id or str(id) of a role.
		Channelid and messageid must be an integer.

	List of commands:
		list
		rm
		post
		update

	When you have configured your table, you can post it to the current channel by executing 'table post [table name]'.
	To get all tables, use 'table list'.
	If you want to change a table, because you want to add/remove a role or change the text, modify the corresponding .json and run 'table update [table name]'.
	It is also possible to remove your table complete via 'table rm [table name]'. !!! BE CAREFULLY WHEN USING THIS COMMAND. This action can not be reverted.  
	"""

	def __init__(self,bot):
		self.bot = bot
		self.jh = Jsonhandel()
		self.utils = Utils(bot, jh = self.jh)
		self.datapath = str(os.path.dirname(os.path.dirname(__file__))) + "/data/giveroles/"
		self.guild = self.bot.get_guild(int(self.jh.getFromConfig("guilde")))

	@commands.group(name = "table", brief = "Manage a table to give/remove roles via reactions.")
	@isBotModCommand()
	async def table(self, ctx):
		"""
		Group of table commands.

		With this command you can post, update or remove a table.
		Tables are used by members to receive roles, when reacting with the specified emoji.
		Also, removing the roles is possible when revoking the reaction.

		More infos can be found via 'help table [command]'.
		"""
		"""
		param ctx:	Discord Context object. Automatical passed.

		Parent command for 'table'.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
		if ctx.invoked_subcommand is None:
			embed = discord.Embed(title = "You need to specify a subcommand. Possible subcommands: post, update, rm, list", color=0xa40000)
			embed.set_author(name = "Invalid command")
			embed.set_footer(text = "For more help run '+help table'")
			await ctx.send(embed = embed, delete_after = 3600)

	@table.command(name = 'list', brief = 'List all tables.')
	@isDMCommand()
	async def list(self, ctx):	
		"""
		Use the command 'table list' to get a list off all tables.
		The list contains the name of a table and the first 20 letters of its text.

		Can only be executed by a bot mod and in the DMs.
		"""
		embed = discord.Embed(title = "List of tables", color = 12008408)
		for table_name, table_text in self.list_table():
			table_text_sanatized = table_text.replace("```","")
			embed.add_field(name = table_name, value = table_text_sanatized[:20] + "..." * (len(table_text_sanatized) > 20), inline=True)
		await ctx.send(embed = embed)

	@table.command(name = 'post', brief = 'Post a table to the channel.')
	@isBotOwnerCommand()
	@isNotInChannelOrDMCommand()
	async def post(self, ctx, table_name):
		"""
		To post a table to a channel, just use the command 'table post [table_name]'.
		The table will be posted the the channel in which the command is invoked.

		Can only be executed by the bot owner and also not in a DM channel.
		"""
		"""
		First checks if the message's reactions are all emojis and if the guild contains all roles.
		Post table to the message channel nd addes the reactions.
		Also save the channel and message id to the table json file.
		"""
		table_content = self.get_table_content(table_name)
		if not table_content:
			await ctx.author.send(f"There is no table with the name {table_name}. See 'table list' to see all tables.", delete_after = 3600)	
			return
		check_res = self.check_content_table(table_content)
		if not check_res[0]:
			await ctx.author.send(f"There is a problem with the config of the table {table_name}. Please check the '{check_res[1]}' roles if they are correct.", delete_after = 3600)
			return
		message = await ctx.channel.send(table_content["text"])
		for emoji in table_content["reactions"].keys():
			await message.add_reaction(emoji)
		table_content["channelid"] = message.channel.id
		table_content["messageid"] = message.id
		await ctx.message.delete()
		self.write_to_json(table_content, table_name)

	@table.command(name = 'rm', brief = 'Removes a table')
	@isBotOwnerCommand()
	@isDMCommand()
	async def rm(self, ctx, table_name):
		"""
		To remove a table the command 'table rm [table_name]' can be used.
		The corresponding table will be deleted from its channel. The config file will remain untouched.

		Can only be executed by the bot owner and also in a DM channel.
		"""
		"""
		First checks if the table with the given name exists. Then checks if the messages can be found via the channel and message id.
		If an error occures, a corresponding message will be send.
		When nothing fails the message will be removed from the channel.
		"""
		table_content = self.get_table_content(table_name)
		if not table_content:
			await ctx.author.send(f"There is no table with the name {table_name}. See 'table list' to see all tables.", delete_after = 3600)
			return
		channel_id = int(table_content["channelid"])
		message_id = int(table_content["messageid"])
		message = await self.get_message(ctx, channel_id, message_id)
		roles_to_remove = [role for (give, remove) in table_content["reactions"].values() for role in remove]
		# Also sorts out users, which discord.Reactions.users() can return.
		remove_from_member = [member for reaction in message.reactions for member in await reaction.users().flatten() if self.guild.get_member(member.id)] 
		for member in remove_from_member:
			await self.utils.removeRoles(member.id, roles_to_remove)
		if not message:
			return
		await message.delete()


	@table.command(name = 'update', brief = 'Updates a table.')
	@isBotOwnerCommand()
	@isDMCommand()
	async def update(self, ctx, table_name):
		"""
		If you want to change a table, then update the config and invoke 'table update [table_name]'.
		The table message will be updated including the changed emojis.

		Can only be executed by the bot owner and also in a DM channel.
		"""
		"""
		First checks if the table with the given name exists. Then checks if the messages can be found via the channel and message id.
		If an error occures, a corresponding message will be send.
		Also tests if the message is from the bot itself. 
		!!! WARNING !!! If a false message/channel id is given, the command can overwritte another bot message. For more details view the command below in the code.
		When nothing fails, reactions will be cleard, the message will be updated and new reactions will be 
		"""
		table_content = self.get_table_content(table_name)
		if not table_content:
			await ctx.author.send(f"There is no table with the name {table_name}. See 'table list' to see all tables.", delete_after = 3600)
			return
		check_res = self.check_content_table(table_content)
		if not check_res[0]:
			await ctx.author.send(f"There is a problem with the config of the table {table_name}. Please check the '{check_res[1]}' roles if they are correct.", delete_after = 3600)
			return
		channel_id = int(table_content["channelid"])
		message_id = int(table_content["messageid"])
		message = await self.get_message(ctx, channel_id, message_id)
		if not message:
			return
		# Test if message is from itself. When fails => message can not be a table.
		# No further test is implemented since there are no identifier for a table and the message/channel id could be modified by the owner.
		# The owner is trusted to specify the correct message/channel id or not to change them.  
		if message.author != self.bot.user:
			await ctx.author.send(f"ERROR: The message with id {message_id} in channel with id {channel_id} is not from the bot itself. Please check the config file for table {table_name}.")
			return
		# Clear all removed reactions
		reactions_to_remove = [reaction for reaction in message.reactions if reaction.emoji.name not in table_content["reactions"].keys()]
		for reaction in reactions_to_remove:
			await message.clear_reaction(reaction.emoji)
		await message.edit(content = table_content["text"])
		present_emojis = [reaction.emoji for reaction in message.reactions]
		emoji_to_add = [emoji for emoji in table_content["reactions"].keys() if emoji not in present_emojis]
		for emoji in emoji_to_add:
			await message.add_reaction(emoji)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		"""
		param payload: 	discord.RawReactionActionEvent object. Automatical passed

		When a member reacts to a table, the corresponding roles will be given.
		"""
		# Ignore bot reactions
		if self.bot.get_user(payload.user_id).bot:
			return
		table_content = self.search_table(payload.channel_id, payload.message_id)
		if not table_content:
			return 
		roles_to_give = table_content["reactions"][payload.emoji.name][0]
		await self.utils.giveRoles(payload.member.id, roles_to_give)

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		"""
		param payload: 	discord.RawReactionActionEvent object. Automatical passed

		When a member reacts to a table, the corresponding roles will be removed.
		"""
		# Ignore bot reactions
		if self.bot.get_user(payload.user_id).bot:
			return
		table_content = self.search_table(payload.channel_id, payload.message_id)
		if not table_content:
			return 
		roles_to_give = table_content["reactions"][payload.emoji.name][1]
		await self.utils.removeRoles(payload.user_id, roles_to_give)

	def search_table(self, channel_id, message_id):
		table_content = None
		for table_name, _ in self.list_table():
			table_temp = self.get_table_content(table_name)
			if str(channel_id) == str(channel_id) and str(message_id) == str(message_id):
				table_content = table_temp
				break
		return table_content

	async def get_message(self, ctx, channel_id, message_id):
		"""
		param ctx:	Discord context 
		param channel_id: 	Id of channel as int
		param message_id: 	Id of message as int

		Trys to retrive a message from the current guild with the give channel and message id. 
		If not found, the ctx.author gets an error message.
		Otherwise returns a Discord message object.
		"""
		channel = self.guild.get_channel(channel_id)
		if not channel:
			await ctx.author.send(f"ERROR: Channel {channel_id} is not found. The configuration of table {table_name} is wrong. Please correct the table by hand in the 'giveroles' folder.")
			return
		message = await channel.fetch_message(message_id)
		if not message:
			await ctx.author.send(f"ERROR: Message {message_id} is not found. The configuration of table {table_name} is wrong. Please correct the table by hand in the 'giveroles' folder.")
			return
		return message

	def get_table_content(self, table_name):
		"""
		param table_name:	String of table_name

		Gets the json Data of a table with the name table_name from '../data/giveroles'.
		The ending '.json' is optional.
		"""
		if not table_name.endswith(".json"):
			table_name += ".json"
		if table_name not in os.listdir(self.datapath):
			return None
		file = self.datapath + table_name
		return json.load(open(file))

	def write_to_json(self, content, table_name):
		"""
		param content:	Dictionary which represents a .json file
		param table_name:	String of table_name

		Gets the json of the specifed table_name and stores content into it.
		The ending '.json' is optional.
		"""
		if not table_name.endswith(".json"):
			table_name += ".json"
		if table_name in os.listdir(self.datapath):
			with open(self.datapath + table_name,'w') as f:
				json.dump(content, f, indent = 6)			

	def list_table(self):
		"""
		Gets the name and text of all tables in the directory '../data/giveroles'.
		"""
		table_list = []
		for table in os.listdir(self.datapath):
			if table.endswith(".json"):
				file = self.datapath + table
				table_content = json.load(open(file))
				table_list.append((table, table_content["text"]))
		return table_list

	def check_content_table(self, content):
		"""
		param content:	Dictionary which represents a .json file

		Checks if the provided content is suitable to be posted as a discord message.
		Investigates if reactions are emojis and if the roles exist on the guild.
		When one test does not pass, False and a reason will be returned as a tuple (False, Reason). Otherwise (True, None) will be returned.
		""" 
		# Check emoji's
		if not set(content["reactions"].keys()).issubset(set(UNICODE_EMOJI['en'].keys())):
			return (False, "EMOJI")
		# Check if roles exist.
		roles = set()
		for tupel in content["reactions"].values():
			for l in tupel:
				for role in l:
					roles.add(role)
		guilde_roles = {role.name for role in self.guild.roles}.union(
			{role.id for role in self.guild.roles},
			{str(role.id) for role in self.guild.roles})
		if not roles.issubset(guilde_roles):
			return (False, "ROLES")
		# Test passed.
		return (True, None)





def setup(bot):
	bot.add_cog(Commandgiverole(bot))