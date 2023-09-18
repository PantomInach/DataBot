import os

import discord
from discord import NotFound
from discord.ext import commands

from helpfunctions.decorators import isBotOwnerCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.textban import Textban
from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle


def hasAnyRole(*items):
    """
    Type:   Decorator for functions with ctx object in args[1].

    param items:    Tuple of Strings and/or integers wit Discord Channel IDs or names.

    Check if a user has any of the roles in items.

    Only use for commands, which USE @commands.command
    commands.has_any_role() does not work in DM since a user can't have roles.
    This one pulls the roles from the configured guild and makes the same check as
    commands.has_any_role().

    Function is not in decorators.py since the Helpfunction Object is needed.
    """

    def predicate(ctx):
        return Commandowner.utils.hasOneRole(ctx.author.id, [*items])

    return commands.check(predicate)


class Commandowner(commands.Cog, name="Bot Owner Commands"):
    """
    You require privilege level 2 to use these commands.
    Only for development and Bot Owner.
    """

    def __init__(self, bot):
        super(Commandowner, self).__init__()
        self.bot = bot
        self.ch = ConfigHandle()
        self.uh = UserHandle()
        self.utils = Utils(bot, ch=self.ch, uh=self.uh)
        self.xpf = Xpfunk()
        self.tban = Textban()

        Commandowner.utils = self.utils

    @commands.command(name="ping")
    @isBotOwnerCommand()
    async def ping(self, ctx):
        await ctx.send("pong pong")

    @commands.command(name="test")
    @isBotOwnerCommand()
    async def test(self, ctx):
        # await ctx.send("Test", view=TestButton())
        await ctx.send("Test", view=TestButton())

    # Starts to log the users in voice channels
    @commands.command(
        name="startlog",
        brief="Starts to log the users on the configured server.",
    )
    @isBotOwnerCommand()
    async def startlog(self, ctx):
        """
        You require privilege level 2 to use this command. Gets the connected users of
        the configured server and increments every second minute their voice XP.
        """
        if self.ch.getFromConfig("log") == "False":
            self.ch.config["log"] = "True"
            self.ch.saveConfig()
            guildID = int(self.ch.getFromConfig("guild"))
            guildName = str(self.bot.get_guild(guildID))
            await self.utils.log(f"Start to log users from Server:\n\t{guildName}", 2)
            # Sets the bot's presence to "Online" to indicate it's logging.
            await self.bot.change_presence(
                status=discord.Status.online,
                activity=discord.Game(
                    str(self.ch.getFromConfig("command_prefix")) + "help"
                ),
            )
        else:
            await ctx.send("Bot is logging. Logging state: True")
        # Sets the bot's presence to "Online" to indicate it's logging.
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                str(self.ch.getFromConfig("command_prefix")) + "help"
            ),
        )

    @commands.command(
        name="stoplog",
        brief="Stops to log the users on configured server.",
    )
    @isBotOwnerCommand()
    async def stoplog(self, ctx):
        """
        You require privilege level 2 to use this command. When the bot logs the connective users on the configured server, this command stops the logging process.
        """
        if self.ch.getFromConfig("log") == "True":
            guildID = int(self.ch.getFromConfig("guild"))
            guildName = str(self.bot.get_guild(guildID))
            self.ch.config["log"] = "False"
            self.ch.saveConfig()
            await self.utils.log(f"Stopped to log users from Server:\n\t{guildName}", 2)
            # Sets the bot's presence to "Do not Disturb" to indicate it's not logging.
            await self.bot.change_presence(
                status=discord.Status.dnd,
                activity=discord.Game(
                    str(self.ch.getFromConfig("command_prefix")) + "help"
                ),
            )
        else:
            await ctx.send("Bot is NOT logging. Logging state: False")

    @commands.command(
        name="stopbot",
        brief="Shuts down the bot.",
    )
    @isBotOwnerCommand()
    async def stopbot(self, ctx):
        """
        You require privilege level 2 to use this command. This command shuts the
        bot down.
        """
        await self.utils.log("[Shut down] Beginning shutdown...", 2)
        # Save json files
        # self.ch.saveConfig()
        # self.ch.saveData()
        await self.utils.log("[Shut down] Files saved", 2)
        # Remove all textbans
        self.tban.removeAllTextBan()
        await self.utils.log("[Shut down] Bot is shutdown", 2)
        # await self.bot.logout()
        await self.bot.close()

    @commands.command(name="changeBotMessage")
    @isBotOwnerCommand()
    async def changeBotMessage(self, ctx, channelID, messageID, text):
        message = await self.bot.get_channel(int(channelID)).fetch_message(
            int(messageID)
        )
        if message.author != self.bot.user:
            await ctx.send("Message is not from bot.")
            return
        if len(text) > 2000:
            await ctx.send("Text is to long")
            return
        await message.edit(content=str(text))

    @commands.command(name="addReaction")
    @isBotOwnerCommand()
    async def addReaction(self, ctx, channelID, messageID, emoji):
        message = await self.bot.get_channel(int(channelID)).fetch_message(
            int(messageID)
        )
        if message.author != self.bot.user:
            await ctx.send("Message is not from bot.")
            return
        try:
            await message.add_reaction(emoji)
        except NotFound:
            await ctx.send("No vaild emoji was sent by user.")

    @commands.command(name="rlext")
    @isBotOwnerCommand()
    async def reloadExtensions(self, ctx, *extensions):
        """
        Reloads cogs.
        """
        """
        param ctx:  Discord Context object.
        param *ext: Names of extensions to be reloaded.

        Reloads given extensions so changes are taken over.
        When no extension is given, all extensions will be reloaded.
        """
        if not extensions:
            extensions = self.bot.extensions.copy()
            list(extensions.keys()).extend(
                [
                    "cogs." + ext[:-3]
                    for ext in os.listdir("./")
                    if ext.endswith(".py") and not ext.startswith("__")
                ]
            )
        reloadedExtensions = []
        for ext in extensions:
            if ext in self.bot.extensions:
                await self.bot.unload_extension(ext)
                await self.bot.load_extension(ext)
                reloadedExtensions.append(ext)
        await self.utils.log(f"Reloaded extensions: {', '.join(reloadedExtensions)}", 2)


class TestButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="test", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        print("Entered callback")
        await interaction.response.send_message("Clicked", ephemeral=False)
        print("After")


async def setup(bot):
    await bot.add_cog(Commandowner(bot))
