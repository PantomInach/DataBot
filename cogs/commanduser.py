import discord
from discord.utils import find
from discord.ext import commands

from helpfunctions.inspiro import Inspiro
from helpfunctions.decorators import isBotModCommand, isDMCommand, isInChannelCommand
from helpfunctions.xpfunk import Xpfunk
from helpfunctions.utils import Utils
from datahandler.textban import Textban
from datahandler.sub import Sub
from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle
from datahandler.commandrights import read_rights_of
from button_views.leaderboard_buttons import LeaderboardButtons

import datetime
import time


def hasAnyRole(*items):
    """
    Type:   Decorator for functions with ctx object in args[1].

    param items:    Tuple of Strings and/or integers wit Discord Channel IDs or names.

    Check if a user has any of the roles in items.

    Only use for commands, which USE @commands.command
    commands.has_any_role() does not work in DM since a users can't have roles.
    This one pulls the roles from the configured guild and makes the same check as
    commands.has_any_role().

    Function is not in decorators.py since the Helpfunction Object is needed.
    """

    def predicate(ctx):
        return Commanduser.utils.hasOneRole(ctx.author.id, [*items])

    return commands.check(predicate)


class Commanduser(commands.Cog, name="User Commands"):
    """
    Class defines user specific commands and functions, which are executed by bot
    commands.

    Commands:
            user get [User ID]
            user rm [User ID]
            user set tc [User ID] [amount]
            user set text [User ID] [amount]
            user set voice [User ID] [amount]
            user star [User ID]
            user tb give [User ID] [time] (reason)
            user tb rm [User ID]
            level
            top
            star

    More info can be found via 'help [command]'.

    All commands in the list below can be executed in this channel.
    """

    utils = None

    roles_userTextban = read_rights_of("userTextban", "roles")
    roles_userStarOfTheWeek = read_rights_of("userStarOfTheWeek", "roles")
    channel_userLevel = read_rights_of("userLevel", "channel")
    channel_userLeaderboard = read_rights_of("userLeaderboard", "channel")
    channel_userGetPicture = read_rights_of("userGetPicture", "channel")

    def __init__(self, bot):
        super(Commanduser, self).__init__()
        # Defines all needed objects
        self.bot = bot
        self.ch = ConfigHandle()
        self.uh = UserHandle()
        self.utils = Utils(bot, ch=self.ch, uh=self.uh)
        self.tban = Textban()
        self.xpf = Xpfunk()
        self.sub = Sub()
        # For hasAnyRole Decorator
        Commanduser.utils = self.utils

    @commands.group(name="user", brief="Group of user commands.")
    async def userParent(self, ctx):
        """
        Used to manage users via the bot.

        Commands:
                user get:   Gives an overview of stored data from the user.
                user rm:    Removes the user data from the stored data.
                user set:   Can set the ex specific data of a user.
                user star:  Gives user 'star of the week' role.
                user tb:    Manages text bans of users.

        More info can be found via 'help [command]'.

        All commands in the list below can be executed in this channel.
        """
        """
        param ctx:  Discord Context object. Automatically passed.

        Is the parent command for the 'user' command.
        When invoked without a sub command an error will be sent. The error message
        will be deleted after an hour.
        """
        if ctx.invoked_subcommand is not None:
            return
        title = (
            "You need to specify a sub command. Possible sub commands:"
            + " get, rm, set, tb, star"
        )
        embed = discord.Embed(
            title=title,
            color=0xA40000,
        )
        embed.set_author(name="Invalid command")
        embed.set_footer(text="For more help run '+help user'")
        await ctx.send(embed=embed, delete_after=3600)

    """
    ######################################################################

    Bot Mod user commands

    ######################################################################
    """

    @userParent.group(name="set", brief="Group of user set commands.")
    @isBotModCommand()
    async def userSetParent(self, ctx):
        """
        This command is used to set the voicexp, textxp, textcount of users.
        Commands:
                user set tc     => sets textcount
                user set voice  => sets voicexp
                user set text   => sets textxp

        Can only be used by bot mods aka user with a privilege level of 1 or higher.

        More info can be found via 'help [command]'.

        All commands in the list below can be executed in this channel.
        """
        """
        param ctx:  Discord Context object. Automatically passed.

        Is the parent command for the 'user set' command.
        When invoked without a sub command an error will be sent. The error message
        will be deleted after an hour.
        """
        if ctx.invoked_subcommand is not None:
            return
        title = (
            "You need to specify a sub command. Possible sub commands:"
            + " voice, text, tc"
        )
        embed = discord.Embed(
            title=title,
            color=0xA40000,
        )
        embed.set_author(name="Invalid command")
        embed.set_footer(text="For more help run '+help user set'")
        await ctx.send(embed=embed, delete_after=3600)

    @userParent.command(name="get", brief="Gets brief user data.")
    @isBotModCommand()
    async def getUserData(self, ctx, userID):
        """
        This command gives you the voicexp, textxp and textcount of a user via
        'user get [userID]'. As an input the user ID is needed.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
        Command: poll get [userID]

        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int

        Sends the user data into the channel.
        """
        if self.uh.isInData(userID):
            voice = self.uh.getUserVoice(userID)
            text = self.uh.getUserText(userID)
            textCount = self.uh.getUserTextCount(userID)
            message = (
                f"User: {str(self.bot.get_user(int(userID)))}"
                + f" VoiceXP: {voice} TextXP: {text} TextCount: {textCount}"
            )
        else:
            user = self.bot.get_user(int(userID))
            message = f"User was not found in data. Created user: {user.mention}"
        await ctx.send(message)

    @userSetParent.command(name="voice", brief="Sets users voicexp")
    async def setVoiceXP(self, ctx, userID, amount):
        """
        Sets users voice xp to given amount via 'user set voice [User ID] [amount]'.
        An integer is needed for the amount.

        Can only be used by bot mods aka user with a privilage level of 1 or higher.
        """
        """
        Command: poll set voice [userID] [amount]

        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int
        param amount:   Integer

        Sets member Voice XP to amount.
        """
        message = ""
        if not self.uh.isInData(userID):
            message = (
                "User was not found in data. Created user: "
                + f"{self.bot.get_user(int(userID))}\n"
            )
            self.uh.addNewDataEntry(userID)
        self.uh.setUserVoice(userID, amount)
        message += (
            f"Set user {str(self.bot.get_user(int(userID)))} voiceXP to {amount}."
        )
        log_message = (
            f"User {ctx.author} set user "
            + f"{str(self.bot.get_user(int(userID)))} voiceXP to {amount}."
        )
        await self.utils.log(
            log_message,
            2,
        )
        await ctx.send(message)

    @userSetParent.command(name="text", brief="Sets users textxp.")
    async def setTextXP(self, ctx, userID, amount):
        """
        Sets users text XP to given amount via 'user set text [userID] [amount]'.
        An integer is needed for the amount.

        Can only be used by bot mods aka user with a privilage level of 1 or higher.
        """
        """
        Command: poll set text <userID> <amount>

        param ctx:  Discord Context object.
        param userID:   Is the userID from discord user as a string or int
        param amount:   Integer

        Sets member Text XP to amount.
        """
        message = ""
        if not self.uh.isInData(userID):
            message = (
                "User was not in data."
                + f" Created user: {self.bot.get_user(int(userID))}\n"
            )
            self.uh.addNewDataEntry(userID)
        self.uh.setUserText(userID, amount)
        message += (
            f"Set user {str(self.bot.get_user(int(userID)))} "
            + f"textXP to {amount}."
        )
        log_message = (
            f"User {ctx.author} set user "
            + f"{str(self.bot.get_user(int(userID)))} textXP to {amount}."
        )
        await self.utils.log(
            log_message,
            2,
        )
        await ctx.send(message)

    @userSetParent.command(name="tc", brief="Sets users text count")
    async def setTextCount(self, ctx, userID, amount):
        """
        Sets users text count to given amount via 'user set tc [userID] [amount]'.
        An integer is needed for the amount.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
        Command: poll set tc [userID] [amount]

        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int
        param amount:   Integer

        Sets member text count to amount.
        """
        message = ""
        if not self.uh.isInData(userID):
            message = (
                "User was not found in data. Created user: "
                + f"{self.bot.get_user(int(userID))}\n"
            )
            self.uh.addNewDataEntry(userID)
        self.uh.setUserTextCount(userID, amount)
        message += (
            f"Set user {str(self.bot.get_user(int(userID)))} TextCount to {amount}."
        )
        log_message = (
            f"User {ctx.author} set user "
            + f"{str(self.bot.get_user(int(userID)))} textCount to {amount}."
        )
        await self.utils.log(
            log_message,
            2,
        )
        await ctx.send(message)

    @userParent.command(name="rm", brief="Removes user from bots data.")
    @isBotModCommand()
    async def removeuser(self, ctx, userID):
        """
        !!! WARNING !!! THIS ACTION IS NOT REVERSIBLE

        Removes the user data from the bot storage via 'user rm [userID]'.

        Can only be used by bot mods aka user with a privilege level of 1 or higher.
        """
        """
        Command: poll rm [userID]

        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int

        Removes user from data.
        """
        if self.uh.removeUserFromData(userID) == 1:
            user = self.bot.get_user(int(userID))
            username = "No User"
            if user:
                username = user.name
            message = f"Removed User {username} with ID {userID} from Data."
        else:
            message = f"User with ID {userID} is not in data."
        await self.utils.log(f"User {ctx.author}: {message}", 2)
        await ctx.send(message)

    """
    ######################################################################

    guild Mod user commands

    ######################################################################
    """

    @userParent.group(name="tb", brief="Group of user text ban commands.")
    @isDMCommand()
    @hasAnyRole(*roles_userTextban)
    async def user_tb_parent(self, ctx):
        """
        This group of commands is use to manage user text bans.
        Text bans are carried out by deleting every message the user writes to that
        guild.

        Commands:
                user tb add [userID] [time] [reason]:   Text bans user
                user tb rm [userID]:            Removes users text ban

        Can only be used in the bot-DM and only by members with one of the roles
        'CEO' or 'COO'.

        More info can be found via 'help [command]'.

        All commands in the list below can be executed in this channel.
        """
        """
        param ctx:  Discord Context object. Automatically passed.

        Is the parent command for the 'user tb' command.
        When invoked without a sub command an error will be sent. The error message
        will be deleted after an hour.
        """
        if ctx.invoked_subcommand:
            return
        embed = discord.Embed(
            title="You need to specify a sub command. Possible sub commands: give, rm",
            color=0xA40000,
        )
        embed.set_author(name="Invalid command")
        embed.set_footer(text="For more help run '+help user tb'")
        await ctx.send(embed=embed, delete_after=3600)

    @user_tb_parent.command(name="give", brief="Text ban a user.")
    async def textban(self, ctx, userID, time, reason):
        """
        Give an user a text ban via 'user tb add [userID] [time] [reason]'.
        Time must be a real number higher equal than '0.1'.
        E.g. '1.4' for a ban over '1.4' hours.
        The reason can be any text.

        The text banned member messages will be immediately removed by the bot.

        Can only be used in the bot-DM and only by members with one of the roles
        'CEO' or 'COO'.

        ! NOTICE ! Currently the text bans will be removed if the bot is restarted.
        """
        """
        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int
        param time: Duration of ban as float. Must be over 0.1.
        param reason:   Reason for text ban.

        Text bans a member by adding them to textban.json.
        Text bans are carried out in main.on_message() by deleting send messages.
        """
        if self.tban.hasTextBan(ctx.author.id):
            content = (
                "ERROR: You aren't allowed to text ban users when you have"
                + " a text ban."
            )
            await ctx.send(
                content=content,
                delete_after=3600,
            )
            return
        if not self.tban.hasTextBan(userID):
            bantime = 0
            # Convert String time to float.
            try:
                bantime = float(time)
            except ValueError:
                bantime = -1
            if bantime >= 0.1:
                # Get member
                user = self.bot.get_user(int(userID))
                guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
                member = guild.get_member(int(userID))
                if user:
                    logchannel = self.bot.get_channel(
                        int(self.ch.getFromConfig("logchannel"))
                    )
                    # Send messages
                    log_message = (
                        f"User {ctx.author.mention} text banned "
                        + f"{user.mention} for {time} h. Reason:\n{reason}"
                    )
                    await self.utils.log(
                        log_message,
                        2,
                    )
                    logchannel_message = (
                        f"{user.mention} was text banned for "
                        + f"{time} h.\n**Reason**: {reason}"
                    )
                    await logchannel.send(logchannel_message)
                    user_message = (
                        f"You received a text ban for {time} h."
                        + f"\n**Reason**: {reason}"
                    )
                    await user.send(content=user_message)
                    mod_message = (
                        f"{member.nick} ({user.name}) was text banned by "
                        + f"{guild.get_member(int(ctx.author.id)).nick} "
                        + f"({ctx.author.name}) for {time} h.\n**Reason**: {reason}"
                    )
                    await self.utils.sendServerModMessage(mod_message)
                    # Textban user and wait till it is over.
                    await self.tban.addTextBan(userID, int(bantime * 3600.0))
                    # Textban over
                    await user.send(
                        "Your text ban is over. Pay more attention to your behavior "
                        + "in the future."
                    )
                else:
                    await ctx.send(
                        content="ERROR! User does not exist.", delete_after=3600
                    )
            else:
                await ctx.send(content="ERROR! Time is not valid.", delete_after=3600)
        else:
            await ctx.send(
                content="ERROR! User has already a text ban.", delete_after=3600
            )

    @user_tb_parent.command(name="rm", brief="Remove a text ban from a user.")
    async def textunban(self, ctx, userID):
        """
        Remove a text ban from a user via 'user tb rm [userID]'.
        Now the user can freely write messages again.

        Can only be used in the DM with the bot and only by users with one of
        the roles 'CEO' or 'COO'.
        """
        """
        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int

        Removes a textban of the given user.
        Textbans are carryed out in main.on_message() by deleting send messages.
        """
        if not self.tban.hasTextBan(ctx.author.id):
            if self.tban.removeTextBan(userID):
                logchannel = self.bot.get_channel(
                    int(self.ch.getFromConfig("logchannel"))
                )
                user = self.bot.get_user(int(userID))
                await self.utils.log(
                    f"User {ctx.author.mention} textunbaned {user.mention}", 2
                )
                await logchannel.send(
                    f"User {ctx.author.mention} textunbaned {user.mention}"
                )
            else:
                await ctx.send(
                    content="ERROR: User has no textban.", delete_after=3600
                )

    """
    # When give star of the week should be queued
    @userParent.command(name = 'star', brief = 'Gives user \'star of the week\'.')
    @isDMCommand()
    @hasAnyRole(*roles_userStarOfTheWeek)
    async def giveStarOfTheWeek(self, ctx, userID):
        ""
        You can give a user 'star of the week' via the command 'user star [user id]'.
        This role should be given as a reward if a user did something great.
        The role will be removed every Monday at 00:00 CET summer time.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO' or 'COO'.
        ""
        ""
        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int

        Gives the chosen member the 'star of the week' role when no one else has the
        role. When someone already has the role, it will be queued to the next Monday
        when no one gets the role.
        ""
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        role = find(lambda role: role.name == "star of the week", guild.roles)
        if role and userID.isdigit() and guild.get_member(int(userID)):
            user = self.bot.get_user(int(userID))
            if role.members:
                # Get next monday in Unix Epoch
                timeWhenNothingInQueue = self._nextWeekdayInUnixEpoch(0)
                # When someone has already the role => Queue in subroutine to give role
                timeString = self.sub.queueGiveRoleOnceAfter(int(userID), role.id, 604800, timeWhenNothingInQueue)
                await self.utils.log(f"User {ctx.author.name} {ctx.author.id} queued {user.name} {user.id} for 'star of the week' on the {timeString}.", 2)
                await ctx.send(f"Member {user.name} will get 'star of the week' on the {timeString}.")

            else:
                # When no one has the role => Give user 'star of the week' immediately
                await self.utils.giveRoles(userID, [role.id])
                await self.utils.log(f"User {ctx.author.name} {ctx.author.id} gave {user.name} {user.id} 'star of the week' threw. +user star ", 2)
                await ctx.send(f"Member {user.name} got 'star of the week' now.")
        else:
            await ctx.send(f"Invalid input. Either userID is not an user on the guild {guild.name} or it is not a ID.")
    """

    @userParent.command(name="star", brief="Gives user 'star of the week'.")
    @isDMCommand()
    @hasAnyRole(*roles_userStarOfTheWeek)
    async def giveStarOfTheWeekNow(self, ctx, userID):
        """
        You can give a user 'star of the week' via the command 'user star [userID]'.
        This role should be given as a reward if a member did something great.
        The role will be removed every Monday at 00:00 CET summer time.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO' or 'COO'.
        """
        """
        param ctx:  Discord Context object.
        param userID:   Is the user ID from discord user as a string or int

        Gives the given user the 'star of the week' role when no one else has the
        role. When someone has the role do nothing.
        """
        guild = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        role = find(lambda role: role.name == "star of the week", guild.roles)
        if role and userID.isdigit() and guild.get_member(int(userID)):
            user = self.bot.get_user(int(userID))
            if role.members:
                # Print Error
                await ctx.send("Someone already has the role 'star of the week'.")

            else:
                # When no one has the role => Give user 'star of the week' immediately
                await self.utils.giveRoles(userID, [role.id])
                await self.utils.log(
                    f"User {ctx.author.name} {ctx.author.id} gave "
                    + f"{user.name} {user.id} 'star of the week' through +user star ",
                    2,
                )
                await ctx.send(f"Member {user.name} got 'star of the week' now.")

    def _nextWeekdayInUnixEpoch(self, toWeekday):
        """
        param weekday:  Which next weekday to output. In [0,6]

        Takes current date and returns next weekday in Unix Epoch.
        """
        today = datetime.date.today()
        nextWeekday = today + datetime.timedelta(
            days=-today.weekday() + toWeekday, weeks=1
        )
        return time.mktime(
            time.strptime(
                f"{nextWeekday.year} {nextWeekday.month} {nextWeekday.day}",
                "%Y %m %d",
            )
        )

    """
    ######################################################################

    Normal @commads.command functions

    ######################################################################
    """

    @commands.command(
        name="level", pass_context=True, brief="Returns the level of a player."
    )
    @isInChannelCommand(*channel_userLevel)
    async def getLevel(self, ctx, *inputs):
        """
        Gives the member a level card via the command 'level'.
        This gives a short overview over the member's stats on the guild.
        By adding a mention or memberID after the command the member can also view the
        levelcard of other members.

        Can only be used in "⏫level" channel.
        """
        """
        param ctx:  Discord Context object.

        Creates an embeded level card of member.
        """
        userID = ctx.author.id
        if inputs:
            userID = (
                str(inputs[0])
                .replace("<", "")
                .replace(">", "")
                .replace("@", "")
                .replace("!", "")
            )
            if not userID.isdigit():
                return
            userID = int(userID)
        server = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
        member = server.get_member(int(userID))
        if not member:
            return
        self.uh.addNewDataEntry(userID)
        # Create Embeded
        avatar_url = member.avatar
        level = self.uh.getUserLevel(userID)
        voiceXP = self.uh.getUserVoice(userID)
        textXP = self.uh.getUserText(userID)
        textCount = self.uh.getUserTextCount(userID)
        nextLevel = self.xpf.xpNeed(voiceXP, textXP)
        embed = discord.Embed(
            title=f"{member.nick}     ({member.name})", color=12008408
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(
            name="HOURS", value=f"{round(int(voiceXP)/30.0,1)}", inline=True
        )
        embed.add_field(name="MESSAGES", value=f"{str(textCount)}", inline=True)
        embed.add_field(
            name="EXPERIENCE",
            value=f"{str(int(voiceXP)+int(textXP))}/{nextLevel}",
            inline=True,
        )
        embed.add_field(name="LEVEL", value=f"{level}", inline=True)
        # Send Embeded
        content = ""
        if userID != ctx.author.id:
            content = ctx.author.mention
        await ctx.send(embed=embed, content=content, delete_after=86400)
        await ctx.message.delete()

    @commands.command(name="top", brief="Sends an interactive rank list.")
    @isInChannelCommand(*channel_userLeaderboard)
    async def leaderboard(self, ctx):
        """
        Spawns an interactive leaderboard in the "⏫level" via the command 'top'.
        Displays the first 10 member with the highest XP total.
        The sites can be changed via reacting with the ⬅️ ➡️ emojis. Use ⬅️ to go
        higher and ➡️ to go lower. With ⏫ you get to the first page.

        Normally the leaderboard is sorted by the total XP. You can see this if 🕰️ 💌
        are reactions. When 🌟 🕰️ are available, it is sorted by messages.
        When 🌟 💌 are available, it is sorted by time on guild.
        You can change the sorting by reacting with 🌟 for total XP, 🕰️
        for time spent on guild and 💌 for total messages send.

        Can only be used in the "⏫level" channel.
        """
        """
        param ctx:  Discord Context object.

        Creates a leaderboard and posts it with the emojis to manipulate it.
        """
        await self.utils.log(f"+top by {ctx.author}", 1)  # Notify Mods
        # Create leaderboard
        text = f"{self.utils.getLeaderboardPageBy(0,0)}{ctx.author.mention}"
        message = await ctx.send(
            text, view=LeaderboardButtons(self.utils), delete_after=86400
        )
        # reactionsarr = ["⏫", "⬅", "➡", "⏰", "💌"]
        # for emoji in reactionsarr:
        #     await message.add_reaction(emoji)
        await ctx.message.delete()

    @commands.command(name="quote", brief="Sends an unique inspirational quote.")
    @isInChannelCommand(*channel_userGetPicture)
    async def getPicture(self, ctx):
        """
        Sent a AI generated inspirational quote via 'quote'.
        These quotes are randomly from 'inspirobot.me'.

        Can only be used in the "🚮spam" channel.
        """
        """
        param ctx:  Discord Context object.

        Sends a AI generated quote from inspirobot.me
        """
        url = Inspiro.getPictureUrl()
        # Create Embeded
        embed = discord.Embed(color=12008408)
        embed.set_image(url=url)
        embed.set_footer(text=url)
        await ctx.send(content=ctx.author.mention, embed=embed)
        await ctx.message.delete()

    """
    Unsupported

    @commands.command(name='reclaimData')
    async def reclaimData(self, ctx, voice, text, textCount, code, hash):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            server = self.bot.get_guild(int(self.ch.getFromConfig("guild")))
            if server.get_member(ctx.author.id) != None:
                if str(voice).isDigit() and str(text).isDigit() and str(textCount).isDigit() and str(code).isDigit():
                    if self.utils.hashDataWithCode(int(voice), int(text), int (textCount), int(code))[0] == hash:
                        self.uh.setUserVoice(ctx.user.id, voice)
                        self.uh.setUserText(ctx.user.id, text)
                        self.uh.setUserTextCount(ctx.user.id, textCount)
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


async def setup(bot):
    await bot.add_cog(Commanduser(bot))
