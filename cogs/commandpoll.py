import discord
from discord.ext import commands

from helpfunctions.decorators import (
    isDMCommand,
    isInChannelOrDMCommand,
    isNotInChannelOrDMCommand,
)
from helpfunctions.utils import Utils
from datahandler.commandrights import read_rights_of
from datahandler.poll import Poll
from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle

from button_views.poll_buttons import PollView


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
        return Commandpoll.utils.hasOneRole(ctx.author.id, [*items])

    return commands.check(predicate)


class Commandpoll(commands.Cog, name="Poll Commands"):
    """
    This bot has the option to host polls. Here is how to do it:

    1) Create a poll:
            You can create a poll by typing 'poll create [poll name]'.
            The poll name must be smaller than 71 characters and will be the title of
            the poll.
            You will get an overview of the poll back. This also includes the poll ID,
            which will be important to configure the poll.
    1.1) List poll:
            By typing 'poll list' you will get an overview of every poll the bot knows
            about.
    2) Add options:
            Use 'poll op add [poll ID] [option name]' to add an option to your poll.
            The option name must be smaller than 113 characters and will be displayed
            in the poll.
    2.1) Remove option:
            By typing 'poll op rm [poll ID] [option name]' you can delete a poll
            option.
    3) View your poll:
            You can use 'poll show [poll ID]' to se an overview of all information
            stored in your poll.
            This shows you the poll message like it will be posted.
    4) Open your poll:
            When you are done with your poll, you can type 'poll open [poll ID]' in
            the channel of your choosing to make it available to vote there.
            The amount of votes per poll option will be updated live in the poll, but
            names of voters won't be shown and stay anonymous to other members.
            You can only open your poll if the overview reads that your poll is
            closed.
    5) Edit your poll:
            Maybe you spot a typo or want to change the poll. Use the command
            'poll close [poll ID]' to close the poll.
            After, you can use 'poll op add [poll ID] [option name]' and
            'poll op rm [poll ID] [option name]' to modify it.
            Just use 'poll open [poll ID]' to reopen it or 'poll rm [poll ID]' to
            delete the poll.
    6) Publish your poll:
            Time's up. If you want to publish the results, you can use
            'poll publish [poll ID]' in the channel of your choosing.
    7) Delete your poll:
            If you want your poll to be deleted type 'poll rm [poll ID]'.
            A request will be automatically send to one of the COOs to delete it for
            you.
    """

    """
    These Commands define interactions with polls.
    """

    utils = None

    roles_pollCreate = read_rights_of("pollCreate", "roles")
    roles_pollShow = read_rights_of("pollShow", "roles")
    roles_optionParent = read_rights_of("optionParent", "roles")
    roles_pollsList = read_rights_of("pollsList", "roles")
    channel_pollsList = read_rights_of("pollsList", "channel")
    roles_pollRemove = read_rights_of("pollsList", "roles")
    roles_pollOpen = read_rights_of("pollOpen", "roles")
    channel_pollOpen = read_rights_of("pollOpen", "channel")
    roles_pollClose = read_rights_of("pollClose", "roles")
    roles_pollPublish = read_rights_of("pollPublish", "roles")
    channel_pollPublish = read_rights_of("pollPublish", "channel")

    def __init__(self, bot):
        super(Commandpoll, self).__init__()
        self.bot = bot
        self.poll = Poll()
        self.ch = ConfigHandle()
        self.uh = UserHandle()
        self.utils = Utils(bot, ch=self.ch, uh=self.uh)
        Commandpoll.utils = self.utils

    @commands.group(name="poll")
    async def poll(self, ctx):
        """
        Group of poll commands.

        This command group is for creating and managing polls.

        How to 'poll':
        1) Create a poll:   'poll create [poll name]'
        1.1) List polls:    'poll list'
        2) Add option:      'poll op add [poll id] [option name]'
        2.1) Remove option: 'poll op rm [poll id] [option name]'
        3) View poll:       'poll show [poll id]'
        4) Open poll:       'poll open [poll id]'
        5) Close poll:      'poll close [poll id]'
        6) Publish poll:    'poll publish [poll id]'
        7) Remove poll:     'poll rm [poll id]'

        For a more indepth explanation for using the poll command, use
        'help Poll Commands'.

        List of all poll commands:
                poll create [poll id]
                poll list
                poll op add [poll id] [option name]
                poll op rm [poll id] [option name]
                poll show [poll id]
                poll open [poll id]
                poll close [poll id]
                poll publish [poll id]
                poll rm [poll id]

        More info can be found via 'help poll [command]'.

        The list of commands below you can execute in this channel.
        """
        """
        param ctx:  Discord Context object. Automatically passed.

        It is the parent command for the 'poll' command.
        When invoked without a subcommand an error will be sent. The error message
        will be deleted after an hour.
        """
        if ctx.invoked_subcommand is not None:
            return
        title = (
            "You need to specify a subcommand. Possible subcommands: "
            + "create, list, show, close, open, publish, rm, op",
        )

        embed = discord.Embed(
            title=title,
            color=0xA40000,
        )
        embed.set_author(name="Invalid command")
        embed.set_footer(text="For more help run '+help poll'")
        await ctx.send(embed=embed, delete_after=3600)

    @poll.command(name="create", brief="Creates a poll.")
    @isDMCommand()
    @hasAnyRole(*roles_pollCreate)
    async def pollCreate(self, ctx, pollName):
        """
        You can create a poll by typing 'poll create [poll name]'.
        The poll name must be smaller than 71 characters and will be the title of
        the poll. You will get an overview of the poll back. This also includes the
        poll ID, which will be important to configure the poll.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollName: String.

        Creates a poll with the given name.
        Poll will have the lowest possible ID.

        Sends an overview of the poll.
        """
        message = ""
        if len(pollName) <= 27:
            pollID = self.poll.newPoll(pollName)
            datum = self.poll.getDate(pollID)
            status = self.poll.getStatus(pollID)
            sumVotes = self.poll.getSumVotes(pollID)
            message = (
                f"```md\n{pollID}\t{pollName}\t{datum}\t{status}\t{sumVotes}\n```\n"
            )
            await self.utils.log(
                f"User {ctx.author} created the poll {pollName} with ID: {pollID}.", 1
            )
        else:
            message = "ERROR: The poll option name is too long."
        await ctx.send(message)

    @poll.command(name="show", brief="Shows an overview of the poll.")
    @isDMCommand()
    @hasAnyRole(*roles_pollShow)
    async def pollShow(self, ctx, pollID):
        """
        You can use 'poll show [poll ID]' to se an overview of all information stored
        in your poll.
        This shows you the poll message like it will be posted.
        Poll ID can be looked up with 'poll list'.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json

        Sends the poll with options to the user.
        Does not change status. Only as a preview.
        """
        message = ""
        if self.poll.isAPollID(pollID):
            message = self.poll.pollString(pollID)
        else:
            message = "ERROR: Poll does not exist. Check +polls for active polls."
        await ctx.send(message)

    @poll.group(name="op", brief="Manipulate options of a poll.")
    @isDMCommand()
    @hasAnyRole(*roles_optionParent)
    async def option_parent(self, ctx):
        """
        Group of poll option commands.

        With this command group, you can add and remove poll options.

        More info can be found via 'help poll op [command]'.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object. Automatically passed.

        It is the parent command for the 'poll op' command.
        When invoked without a subcommand an error will be sent. The error message
        will be deleted after an hour.
        """
        if ctx.invoked_subcommand is not None:
            return
        embed = discord.Embed(
            title="You need to specify a subcommand. Possible subcommands: add, rm",
            color=0xA40000,
        )
        embed.set_author(name="Invalid command")
        embed.set_footer(text="For more help run '+help poll op'")
        await ctx.send(embed=embed, delete_after=3600)

    @option_parent.command(name="add", brief="Add potion to a poll")
    async def optionAdd(self, ctx, pollID, optionName):
        """
        Use 'poll op add [poll id] [option name]' to add an option to your poll.
        The option name will be displayed in the poll.

        Can only be used if the poll is closed.
        The option name must be smaller than 113 characters and there can only be
        7 options.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json
        param optionName:   String.

        Tries to add an option to the poll with optionName.
        New option gets the lowest possible optionID.
        """
        message = ""
        if self.poll.isAPollID(pollID):
            if len(optionName) <= 70:
                if not self.poll.optionAdd(pollID, str(optionName), 0):
                    message = (
                        "ERROR: Option Name is already taken or poll is "
                        + "not CLOSED. Try another.\n"
                    )
                message += f"{self.poll.pollString(pollID)}"
            else:
                message = "ERROR: OptionName is too long."
        else:
            message = (
                "ERROR: Poll does not exist. Check `poll list` for all known polls."
            )
        await ctx.send(message)

    @option_parent.command(name="rm", brief="Remove an option from a poll.")
    async def polloptionRemove(self, ctx, pollID, optionName):
        """
        If you want to remove an option, it will be possible with
        'poll op rm [poll id] [option name]'.

        Can only be used if the poll is closed.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json
        param optionName:   String.

        Tries to remove an option from the poll with option name.
        All option IDs higher than the removed option will decremented.
        """
        message = ""
        if self.poll.isAPollID(pollID):
            if not self.poll.optionRemove(pollID, str(optionName)):
                message = (
                    "ERROR: Could not find option name or poll"
                    + " is not CLOSED. Try another Name.\n"
                )
            message += f"{self.poll.pollString(pollID)}"
        else:
            message = (
                "ERROR: Poll does not exist. Check `poll list` for all known polls."
            )
        await ctx.send(message)

    @poll.command(name="list", brief="Gives Overview of all polls.")
    @isInChannelOrDMCommand(*channel_pollsList)
    @hasAnyRole(*roles_pollsList)
    async def pollsList(self, ctx):
        """
        With 'poll list' you will get an overview of every poll the bot knows about.
        This includes 'poll ID', 'poll name', 'date of creation', 'status'
        and 'votes'.

        Can only be used in the bot-DM or in the '🚮spam' channel and only by
        members with one of the roles 'CEO', 'COO', 'chairman' or 'associate'.
        """
        """
        param ctx:  Discord Context object.

        Sends the header of all polls in poll.json.
        """
        message = ""
        for pollID in self.poll.getAllPolls()[::-1]:
            message += self.poll.pollHeader(pollID)
        if message == "":
            message = "No active polls."
        await ctx.send(message)

    @poll.command(name="rm", brief="Removes a poll.")
    @isDMCommand()
    @hasAnyRole(*roles_pollRemove)
    async def poll_remove(self, ctx, pollID):
        """
        To add an option to a poll use the command
        'poll op add [poll id] [option name]'

        Can only be used if the poll is closed.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json

        Removes a poll from poll.json if requirements are meet.
        """
        message = ""
        if self.poll.isAPollID(pollID):
            pollName = self.poll.getName(pollID)
            if (
                len(self.poll.getOptions(pollID)) == 0
                or self.ch.getPrivilegeLevel(ctx.author.id) >= 1
                or self.utils.hasRole(ctx.author.id, "chairman")
            ):
                if self.poll.removePoll(pollID):
                    message = f"Removed Poll {pollName}."
                    await self.utils.log(
                        f'User {ctx.author.mention} removed the poll: "{pollName}".',
                        2,
                    )
                    channel = self.bot.get_channel(
                        int(self.ch.getFromConfig("logchannel"))
                    )
                    await channel.send(
                        f'User {ctx.author.mention} removed the poll: "{pollName}".'
                    )
                else:
                    message = "ERROR: Something strange happened."
                    await self.utils.log(
                        f'User {ctx.author.name} tried to remove poll: "{pollName}",'
                        + f" {pollID} with message: {ctx.message.content}"
                    )
            else:
                message = (
                    "Can't remove a poll with options. Contacted Bot Mods to"
                    + " review your command. The poll will maybe be removed."
                )
                await self.utils.sendServerModMessage(
                    f"User {ctx.author.mention} wants to remove the poll: "
                    + f'"{pollName}". Use Command "poll rm {pollID}" '
                    + "to remove the poll."
                )
        else:
            message = (
                "ERROR: Poll does not exist. Check `poll list` for all known polls."
            )
        await ctx.send(message)

    @poll.command(name="open", brief="Opens a poll.")
    @isNotInChannelOrDMCommand(*channel_pollOpen)
    @hasAnyRole(*roles_pollOpen)
    async def poll_open(self, ctx, pollID):
        """
        To open a poll use the command 'poll open [poll id]'.
        The poll will be posted like in 'poll show' into the channel, in which the
        command is invoked. Also, reactions will be added, which enable a member to
        vote on the option. The amount of votes will be shown in real time in the
        poll.

        Can only be used if the poll is closed.

        Can not be used in the "📂log","📢info","⏫level" channel or bot-DM and can be
        only by members with one of the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json

        Posts a poll to channel, adds reactions to vote for options and opens poll.
        """
        [messageID, channelID] = self.poll.getMessageID(pollID)
        self.poll.pollOpen(pollID)
        # Test if it has a send poll string somewhere
        if messageID and channelID:
            # poll has been sent somewhere => delete old one
            channel = self.bot.get_channel(int(channelID))
            if channel:
                try:
                    messageToDelet = await channel.fetch_message(int(messageID))
                    await messageToDelet.delete()
                except discord.NotFound:
                    pass
        # Poll is open => send it
        if self.poll.getStatus(pollID) == "OPEN":
            # Send poll
            text = self.poll.pollString(pollID)
            button_amount = len(self.poll.getOptions(pollID))
            pollView = PollView(button_amount, self.poll, pollID)
            messageSend = await ctx.send(
                content=f"{text}{ctx.author.mention}", view=pollView
            )
            self.poll.setMessageID(pollID, messageSend.id, messageSend.channel.id)
            log_message = (
                f"User {ctx.author.mention} opened the poll {pollID}"
                + f" in channel {ctx.channel.name}."
            )
            await self.utils.log(
                log_message,
                1,
            )
        elif self.poll.getStatus(pollID) == "CLOSED":
            message = "ERROR: You can't open a poll with only 1 poll option"
            await ctx.author.send(message)
        await ctx.message.delete()

    @poll.command(name="close", brief="Closes a poll.")
    @isDMCommand()
    @hasAnyRole(*roles_pollClose)
    async def poll_close(self, ctx, pollID):
        """
        Closing a poll can be done by the command 'poll close [poll id]'.
        Now the poll can be edited again via 'poll op add/rm'.
        Also the posted poll will be edited to show that it is closed and the
        reactions will be removed.

        Can only be used if the poll is OPEN.

        Can only be used in the bot-DM and only by members with one of
        the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json

        Sets status of poll to CLOSED and removes reactions from poll, so nobody
        can vote anymore.
        """
        [messageID, channelID] = self.poll.getMessageID(pollID)
        closed = self.poll.pollClose(pollID)
        if closed:
            await self.utils.log(
                f'User {ctx.author.name} cloesed poll: "{self.poll.getName(pollID)}"',
                1,
            )
        if not (closed and messageID and channelID):
            await ctx.send("ERROR POLL STATUS: Can't close Poll.")
            return
        # Edit message
        channel = self.bot.get_channel(int(channelID))
        if not channel:
            return
        try:
            message = await channel.fetch_message(int(messageID))
            await message.edit(content=f"{self.poll.pollString(pollID)}", view=None)
            # self.poll.setMessageID(pollID, '', '')
        except discord.NotFound:
            return

    @poll.command(name="publish", brief="Publishes a poll.")
    @isNotInChannelOrDMCommand(*channel_pollPublish)
    @hasAnyRole(*roles_pollPublish)
    async def poll_publish(self, ctx, pollID):
        """
        To publish a poll use the command 'poll publish [poll id]'.
        The poll will be posted like in 'poll show' to the channel, in which the
        command is invoked. Published polls can not be altered and give the final
        result of a poll.

        Can only be used if the poll is open.

        Can not be used in the "📂log","📢info","⏫level" channel or bot-DM and only by
        members with one of the roles 'CEO', 'COO' or 'chairman'.
        """
        """
        param ctx:  Discord Context object.
        param pollID:   Integer. ID of a poll in poll.json

        Sets status of poll to published and removes reactions from poll, so
        nobody can vote anymore.
        """
        await ctx.message.delete()
        published = self.poll.pollPublish(pollID)
        if not published:
            await ctx.send(
                content="ERROR: Poll does not exist or poll is not OPEN.",
                delete_after=7200,
            )
            return
        # Delete OPEN poll to resend as published
        [messageID, channelID] = self.poll.getMessageID(pollID)
        channel = self.bot.get_channel(int(channelID))
        if not channel:
            return
        try:
            message = await channel.fetch_message(int(messageID))
            await message.delete()
        except discord.NotFound:
            pass
        # Send published poll
        text = self.poll.pollStringSortBy(pollID, 1)
        message = await ctx.send(content=text)
        self.poll.setMessageID(pollID, "", "")
        # Give voters XP
        for vote in self.poll.getVotes(pollID):
            self.uh.addTextXP(vote[0], 25)


async def setup(bot):
    await bot.add_cog(Commandpoll(bot))
