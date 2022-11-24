import discord
from discord.ext import commands

from helpfunctions.decorators import isBotModCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.jsonhandel import Jsonhandel


class Commandmod(commands.Cog, name="Bot Mod Commands"):
    """
    Group of 'Bot Mod' commands.

    Commands to manage no critical settings of the bot.

    List of commands:
            textwl add (channelID)
            textwl rm (channelID)
            voicebl add (channelID)
            voicebl rm (channelID)
            dp

    More info can be found via 'help textwl', 'help voicebl' and 'help dp'.

    All commands in the list below can be executed in this channel.
    """

    def __init__(self, bot):
        super(Commandmod, self).__init__()
        self.bot = bot
        self.jh = Jsonhandel()
        self.utils = Utils(bot, jh=self.jh)
        self.xpf = Xpfunk()

    """
	######################################################################

	Text Whitelist commands and function

	######################################################################
	"""

    @commands.group(
        name="textwl", brief="Add or remove a text channel to be logged by the bot."
    )
    @isBotModCommand()
    async def textwl(self, ctx):
        """
        Group of text whitelist commands.

        This command group is for managing the text whitelist.
        When a message is sent to a whitelisted text channel and the bot can see the message, the author of this message will get XP.

        Use \'textwl add [channelID]\' or use \'textwl add\' in a channel to add it to the whitelist.
        Use \'textwl rm [channelID]\' or use \'textwl rm\' in a channel to remove it from the whitelist.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.

        More info can be found via 'help textwl [command]'.

        All commands in the list below can be executed in this channel.
        """
        """
		param ctx:	Discord Context object. Automatically passed.

		It is the parent command for the 'textwl' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="You need to specify a subcommand. Possible subcommands: add, remove",
                color=0xA40000,
            )
            embed.set_author(name="Invalid command")
            embed.set_footer(text="For more help run '+help textwl'")
            await ctx.send(embed=embed, delete_after=3600)

    @textwl.command(name="add", brief="Adds a channel to the whitelist")
    async def addtextwhitelist(self, ctx, channelID=None):
        """
        Adds a text channel to the whitelist.

        You can obtain the channel ID by right-clicking on a channel and pressing 'copy ID' when you have developer options enabled.
        Also, it is possible to add a text channel to the whitelist by writing 'textwl add' into it.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channel ID. Default is None.

		Adds channel to whitelist, so users can get XP in the channel.
		"""
        guild = self.bot.get_guild(self.jh.getFromConfig("guild"))
        channels = self.bot.guilds[0].text_channels
        # When channelID is not given, use ctx.channel.id.
        if not channelID:
            channelID = ctx.channel.id
        # Test if channel is in Server
        if str(channelID) in [str(channel.id) for channel in channels]:
            # Try to write in whitelist
            if self.jh.writeToWhitelist(channelID):
                channelName = str(self.bot.get_channel(int(channelID)))
                message = f"Added {channelName} with ID {channelID} to whitelist. This Text channel will be logged."
            else:
                message = "Channel is already in whitelist."
        else:
            message = f"Channel is not in the server {str(guild)}"
            await self.utils.log(f"{message} from user {ctx.author}", 2)
        await ctx.send(message)

    @textwl.command(name="rm", brief="Removes a text channel from the whitelist")
    async def removetextwhitelist(self, ctx, channelID=None):
        """
        Removes a text channel from the whitelist.

        You can obtain the channel ID by right-clicking on a channel and pressing 'copy ID' when you have developer options enabled.
        Also, it is possible to remove a text channel from the whitelist by writing 'textwl rm' into it.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channel ID. Default is None.

		Removes channel from whitelist, so users can not get XP in the channel.
		"""
        # When channelID is not given, use ctx.channel.id.
        if not channelID:
            channelID = ctx.channel.id
        # Try to remove from whitelist
        if self.jh.removeFromWhitelist(channelID):
            channelName = str(self.bot.get_channel(int(channelID)))
            message = f"Removed {channelName} with ID {channelID} from Whitelist. This Text channel will not be logged."
        else:
            message = "Channel does not exist or is not in Whitelist"
            await self.utils.log(f"{message} from user {ctx.author}", 2)
        await ctx.send(message)

    """
	######################################################################

	Voice Blacklist commands and function

	######################################################################
	"""

    @commands.group(name="voicebl")
    @isBotModCommand()
    async def voicebl(self, ctx):
        """
        Group of voice blacklist commands.

        This command group is for managing the voice blacklist.
        In a predefined time interval the bot scans all voice channels for aktive members to give them voive XP. When the channel is on the blacklist, aktive members will be ignored.

        Use \'voicebl add [channelID]\' to add a channel to the blacklist.
        Use \'voicebl rm [channelID]\' to remove it from the blacklist.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.

        More info can be found via 'help voicebl [command]'.

        All commands in the list below can be executed in this channel.
        """
        """
		param ctx:	Discord Context object. Automatically passed.

		It is the parent command for the 'voicebl' command.
		When invoked without a subcommand an error will be sent. The error message will be deleted after an hour.
		"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="You need to specify a subcommand. Possible subcommands: add, remove",
                color=0xA40000,
            )
            embed.set_author(name="Invalid command")
            embed.set_footer(text="For more help run '+help voicebl'")
            await ctx.send(embed=embed, delete_after=3600)

    @voicebl.command(name="add", brief="Add a voice channel to the blacklist.")
    async def addblacklist(self, ctx, channelID):
        """
        Adds a voice channel to the blacklist.

        You can obtain the channel ID by right-clicking on a channel and pressing 'copy ID' when you have developer options enabled.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channel ID.

		Adds channel to whitelist, so users can not get XP in the channel.
		"""
        guild = self.bot.get_guild(self.jh.getFromConfig("guild"))
        channels = self.bot.guilds[0].voice_channels
        # Test if channel is in Server
        if str(channelID) in [str(channel.id) for channel in channels]:
            # Try to write in Blacklist
            if self.jh.writeToBalcklist(channelID):
                channelName = str(self.bot.get_channel(int(channelID)))
                message = f"Added {channelName} with ID {channelID} to blacklist. This Voice channel will not be logged."
            else:
                message = "Channel is already in blacklist."
        else:
            message = f"Channel is not in the server {str(guild)}"
        await self.utils.log(f"{message} from user {ctx.author}", 2)
        await ctx.send(message)

    @voicebl.command(name="rm", brief="Removes a voice channel from the blacklist.")
    async def removeblacklist(self, ctx, channelID=None):
        """
        Removes a voice channel from the blacklist.

        You can obtain the channel ID by right-clicking on a channel and pressing 'copy ID' when you have developer options enabled.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
		param ctx:	Discord Context object.
		param channelID:	Integer or String of channel ID. Default is None.

		Removes channel from whitelist, so users can get XP in the channel.
		"""
        # When channelID is not given, use ctx.channel.id.
        if not channelID:
            channelID = ctx.channel.id
        if self.jh.removeFromBalcklist(channelID):
            channelName = str(self.bot.get_channel(int(channelID)))
            message = f"Removed {channelName} with ID {channelID} from blacklist. This Voice channel will be logged."
        else:
            message = "Channel does not exist or is not in blacklist"
        await self.utils.log(f"{message} from user {ctx.author}", 2)
        await ctx.send(message)

    """
	######################################################################

	Normal @commads.command functions

	######################################################################
	"""

    @commands.command(name="dp", brief="Prints the Data of the Users")
    @isBotModCommand()
    async def printData(self, ctx):
        """
        Prints the Username, userID, level, voiceXP, textXP and textCount off all members on the server.
        If the user is not in the guild anymore, the name will be replaced by 'No User'.

        Can only be used by bot mods aka the user with a privilege level of 1 or higher.
        """
        """
		param ctx:	Discord Context object. Automatically passed.

		Prints all user data in format:
			User: "Username", UserID: User ID, Level: int, VoiceXP: int, TextXP: int, Messages: int.
		"""
        guild = str(self.bot.get_guild(int(self.jh.getFromConfig("guild"))))
        message = f"Printing data of server {guild}:\n"
        # Sorts user by their usernames
        sortedData = sorted(
            self.jh.data,
            key=lambda id: str(self.bot.get_user(int(id)).name).lower()
            if self.bot.get_user(int(id)) != None
            else "no user",
        )
        for userID in sortedData:
            level = self.jh.getUserLevel(userID)
            voiceXP = self.jh.getUserVoice(userID)
            textXP = self.jh.getUserText(userID)
            textCount = self.jh.getUserTextCount(userID)
            user = self.bot.get_user(int(userID))
            username = "No User"
            # Handel not existing User IDs
            if user != None:
                username = user.name
            # Message format
            messageadd = f"\nUser: {username}, UserID: {userID}, Level: {level}, VoiceXP: {voiceXP}, TextXP: {textXP}, Messages: {textCount}."
            if (
                len(message) + len(messageadd) > 1994
            ):  # Get around 2000 char discord text limit
                await ctx.send(f"```message```")
                message = ""
            message += messageadd
        print(f"User {ctx.author} prints all data in {ctx.channel}.")
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Commandmod(bot))
