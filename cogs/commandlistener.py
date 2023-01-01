import discord
from discord.ext import commands
from discord.utils import find
import traceback
import sys

from helpfunctions.utils import Utils
from helpfunctions.xpfunk import Xpfunk
from datahandler.jsonhandle import Jsonhandle
from datahandler.textban import Textban


class Commandlistener(commands.Cog):
    """
    Contains general purpose listeners for bot.
    """

    def __init__(self, bot):
        self.bot = bot
        self.jh = Jsonhandle()
        self.utils = Utils(bot, jh=self.jh)
        self.xpf = Xpfunk()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )
        errorMessage = traceback.format_exception(
            type(error), error, error.__traceback__
        )
        Utils.logToFile(
            f"Ignoring exception in command {ctx.command}\n"
            + ("\n".join(errorMessage)),
            withDate=True,
        )
        embed = discord.Embed(
            title=f"Ignoring exception in command {ctx.command}",
            description="\n".join(errorMessage).replace("**", "\\*\\*"),
            color=0xEF2929,
        )
        await self.utils.sendModsMessage("", embed=embed)

    # When bot is connected
    @commands.Cog.listener()
    async def on_ready(self):
        # Sends message to mods, when bot is online
        print("Now Online")
        await self.utils.sendModsMessage(
            "Bot is now online.\nVersion:\tDiscordBot DataBot v2.0.1"
        )

    # When a member joins a guild
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        param member:   User on guild

        Creates a welcome message in the log channel
        """
        channel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
        guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
        await channel.send(f"Hey **{member.mention}**, welcome to {guild}")

    """
    @commands.Cog.listener()
    async def on_disconnect(self):
        owner = self.bot.get_user(int(self.jh.getFromConfig("owner")))
        await self.utils.sendOwnerMessage("Bot is offline.")
    """

    # When a member leaves the guild
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        param member:   User on guild

        Sends a goodbye message in the log channel
        """
        channel = self.bot.get_channel(int(self.jh.getFromConfig("logchannel")))
        guild = self.bot.get_guild(int(self.jh.getFromConfig("guild")))
        await channel.send(
            f"**{member.name}** has left {guild}. Press F to pay respect."
        )
        """
        #Hash user data
        voice = jh.getUserVoice(member.id)
        text = jh.getUserText(member.id)
        textCount = jh.getUserTextCount(member.id)
        [hash, code] = self.utils.hashData(voice, text, textCount, member.id)
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
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        param payload:  Gives context about the added reaction

        Handles different self.bot interactions with the server via reactions.

        First:
                Handles leaderboard interactions for new page and new sorting.
        Second:
                Handles voting on polls.
        Third:
                Give role on data processing.
        Forth:  (Handled in commandpoll.py)
                Handles reactions on interest groups for user to get roles.
        Fifth:
                Give XP when a reaction is added.
        Sixth:
                Give role of giveRoles message.
        """

        # Ignore self.bot reactions
        if self.bot.get_user(payload.user_id).bot:
            return

        channel = self.bot.get_channel(int(payload.channel_id))
        message = await channel.fetch_message(int(payload.message_id))
        [state, page] = Utils.getMessageState(message)
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
        if state in range(1, 4):
            # Handel Leaderboard reactions
            change = self._getLeaderboardChange(message)
            """
            change:
                0: to first page
                1: page before
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
                choice = [0, page - 1 if page - 1 >= 0 else 0, page + 1]
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

            text = self.utils.getLeaderboardPageBy(page, sortBy)
            if text == "":
                # If no one is on this page, get last page.
                text = self.utils.getLeaderboardPageBy(page - 1, sortBy)

            # Changes Leaderboard and adds reactions
            await message.edit(content=f"{text}{payload.member.mention}")
            if change >= 3:
                # When all reactions were wiped. Added new Reactions
                reactionsarr = ["⏫", "⬅", "➡", "⏰", "💌", "🌟"]
                removeemoji = [5, 3, 4]
                del reactionsarr[removeemoji[sortBy]]
                for emoji in reactionsarr:
                    await message.add_reaction(emoji)

        # Member is reacting to other members and gets XP
        else:
            # Give reaction XP
            channel = self.bot.get_channel(payload.channel_id)
            if self.jh.isInWhitelist(payload.channel_id):
                message = await channel.fetch_message(payload.message_id)
                if (
                    not (message.author.bot or payload.member.bot)
                    and self.jh.getFromConfig("log") == "True"
                ):
                    self.jh.addReactionXP(payload.user_id, self.xpf.randomRange(1, 5))
                    self.jh.saveData()

    # When a user changes his voice state
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Handles user interactions when a user changes his voice state.
        A voice change is when a member changes/joins a channel,
        mutes/unmutes themselves, deafens/undeafens themselves.

        param member:   User on guild
        param before:   Gives the voice state before the change
        param after:    Gives the voice state after the change

        First:
                Handles voice channel deletion when a user leaves a voice channel
                and no one else is connected to it.
        Second:
                Creates a new voice channel when all other channels
                with numbers at the end of its name are occupied.
        """
        # when user joins channel: before = None; after is a voice state

        allChannel = self.bot.guilds[0].voice_channels
        """
        When a user leaves a channel (before.channel) with a number at the end,
        nobody else is connected and and number is not 1,
        then the channel will be deleted.
        """
        if (
            before.channel
            and len(before.channel.members) == 0
            and before.channel.name[-1].isdigit()
        ):
            # Member left first channel
            if before.channel.name[-1] == "1" and not before.channel.name[-2].isdigit():
                # Delete last channel, which has no user in it

                channelWithoutNumber = before.channel.name[:-1]
                notFirstVoiceChannel = [
                    channel
                    for channel in allChannel
                    if channelWithoutNumber in channel.name
                    and len(channel.members) == 0
                    and channel.name != channelWithoutNumber + "1"
                ]
                if notFirstVoiceChannel:
                    lastChannel = max(
                        notFirstVoiceChannel,
                        key=lambda c: int(c.name[len(channelWithoutNumber):]),
                    )

                    # Removes channel from blacklist if necessary
                    self.jh.removeFromBalcklist(lastChannel.id)

                    await lastChannel.delete()

            # User left channel, which is not the first channel. So it will be deleted
            else:
                # Removes channel from blacklist if necessary
                self.jh.removeFromBalcklist(before.channel.id)
                await before.channel.delete()

        """
        User joins channel after.channel. If channel ends with a number,
        then a copy will be created with the lowest other number at the end.
        """
        if (
            after.channel
            and before.channel != after.channel
            and len(after.channel.members) <= 1
        ):
            # Get channels to get lowest enumeration of channel
            afterNumber = None
            nameIndex = -1
            while after.channel.name[nameIndex:].isdigit():
                afterNumber = int(
                    after.channel.name[nameIndex:]
                )  # number at the end of channel name
                nameIndex -= 1
            nameIndex += 1

            channelWithoutNumber = after.channel.name[:nameIndex]
            # When after.channel name ends with number and channel number 1 has user
            # in it
            if afterNumber and len(
                find(
                    lambda c: c.name == (channelWithoutNumber + "1"), allChannel
                ).members
            ):
                # Get channels with after.channel.name without numbers in it and end
                # with digits
                voiceChanelsWithName = [
                    channel
                    for channel in allChannel
                    if after.channel.name[:nameIndex] in channel.name
                    and channel.name[len(channelWithoutNumber):].isdigit()
                ]
                # Get all numbers in the end of voiceChannelsWithName
                numbersOfChannels = [
                    int(channel.name[len(channelWithoutNumber):])
                    for channel in voiceChanelsWithName
                ]
                lowestFreeID = min(
                    [
                        i
                        for i in range(2, max(numbersOfChannels) + 2)
                        if i not in numbersOfChannels
                    ]
                )

                channelWithNumberBefore = find(
                    lambda c: c.name[-len(str(lowestFreeID - 1)):]
                    == str(lowestFreeID - 1),
                    voiceChanelsWithName,
                )
                newChannelName = channelWithoutNumber + str(lowestFreeID)
                # Creates channel and gets it
                newChannel = await channelWithNumberBefore.clone(name=newChannelName)

                if self.jh.isInBlacklist(after.channel.id):
                    self.jh.writeToBalcklist(newChannel.id)

                # Move channel after channelWithNumberBefore
                await newChannel.move(after=channelWithNumberBefore)

    # When bot reads a message
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        param message:  Message read by the bot

        Ignore bot messages
        """
        if message.author == self.bot.user:
            return

        # Delete messages if user is text banned
        if Textban.staticHasTextBan(int(message.author.id)) and not isinstance(
            message.channel, discord.channel.DMChannel
        ):
            await message.delete()
            return

        a = "" + message.content

        # Stops user from writting in levelchannel none command messages
        if str(message.channel.id) == str(self.jh.getFromConfig("levelchannel")) and a[
            0
        ] != self.jh.getFromConfig("command_prefix"):
            await message.delete()
            return

        # Checks if message contains a picture
        if len(message.attachments) > 0 and self.jh.getFromConfig("log") == "True":
            attachments = message.attachments
            userID = message.author.id
            for attachment in attachments:
                name = attachment.filename
                if name.endswith("jpg") or name.endswith("png"):
                    # Gives XP when picture is in message
                    self.jh.addTextXP(userID, self.xpf.randomRange(20, 40))
                    self.jh.saveData()
                    return

        # When Message is a String
        if (
            a != ""
            and a[0] != self.jh.getFromConfig("command_prefix")
            and self.jh.getFromConfig("log") == "True"
        ):
            # Give XP when message is not a command
            if self.jh.isInWhitelist(message.channel.id):
                self.jh.addTextXP(message.author.id, self.xpf.textXP(a))
                self.jh.saveData()

        # Sends BotOwner commands, which are triggering the bot
        if len(a) > 0 and a[0] == self.jh.getFromConfig("command_prefix"):
            channelName = "DM"
            try:
                channelName = message.channel.name
            except Exception:
                channelName = "DM"
            string = (
                "\n```User "
                + str(message.author.name)
                + "tried to invoke a command in "
                + str(channelName)
                + ".\nCommand: "
                + a
                + "```\n"
            )
            await self.utils.log(string, 2)

    def _getLeaderboardChange(self, message):
        """
        param message:  Discord Message object. Should be from a leaderboard.

        Gets how to change the leaderboard depending on its reactions.

        Return:
                0: to first page
                1: page before
                2: page after
                3: sort xp
                4: sort voice
                5: sort textcount
        """
        reactions = message.reactions
        i = 0
        while reactions[i].count == 1:
            i += 1
        if str(reactions[i]) == "🌟":
            i = 3
        elif str(reactions[i]) == "⏰":
            i = 4
        elif str(reactions[i]) == "💌":
            i = 5
        elif i > 5:
            i = 6
        return i


async def setup(bot):
    await bot.add_cog(Commandlistener(bot))
