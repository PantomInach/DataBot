import discord
from enum import Enum

from datahandler.tempLeaderboard import SortBy


class SortedByEnum(Enum):
    XP = 0
    VOICE = 1
    MESSAGES = 2


class LeaderboardButtons(discord.ui.View):
    def __init__(self, utils, timeFrame=None):
        self.sorted_by = SortedByEnum.XP
        self.timeFrame = timeFrame
        self.utils = utils
        super().__init__(timeout=None)

    # @discord.ui.button(label="Page:", row=0, disabled=True, style=discord.ButtonStyle.secondary)
    # async def page_spacer(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="TOP", row=0, style=discord.ButtonStyle.primary, emoji="⏫"
    )
    async def go_to_page_one(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Go to page one'")
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            if page != 0:
                leaderboard_text = self._getLeaderBoard(0, self.sorted_by)
                try:
                    await message.edit(content=leaderboard_text, view=self)
                except Exception as e:
                    await interaction.response.send_message(
                        "Internal Bot ERROR", ephemeral=True
                    )
                    print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="UP", row=0, style=discord.ButtonStyle.primary, emoji="⬆"
    )
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Go to previous page'")
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            if page != 0:
                page -= 1
                leaderboard_text = self._getLeaderBoard(page, self.sorted_by)
                try:
                    await message.edit(content=leaderboard_text, view=self)
                except Exception as e:
                    await interaction.response.send_message(
                        "Internal Bot ERROR", ephemeral=True
                    )
                    print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="DOWN", row=0, style=discord.ButtonStyle.primary, emoji="⬇"
    )
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            page += 1
            leaderboard_text = self._getLeaderBoard(page, self.sorted_by)
            while leaderboard_text == "":
                if page <= -1:
                    print("Error: Can't get leaderboard with content")
                    await interaction.response.defer(ephemeral=False)
                    return
                page -= 1
                leaderboard_text = self._getLeaderBoard(page, self.sorted_by)
            try:
                await message.edit(content=leaderboard_text, view=self)
            except Exception as e:
                await interaction.response.send_message(
                    "Internal Bot ERROR", ephemeral=True
                )
                print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    # @discord.ui.button(label="Sort by", row=1, disabled=True, style=discord.ButtonStyle.secondary)
    # async def sort_by_spacer(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="EXP", row=1, style=discord.ButtonStyle.primary, emoji="🌟"
    )
    async def sort_by_xp(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Sort by experience'")
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            if self.sorted_by != SortedByEnum.XP:
                self.sorted_by = SortedByEnum.XP
                leaderboard_text = self._getLeaderBoard(page, SortedByEnum.XP)
                try:
                    await message.edit(content=leaderboard_text, view=self)
                except Exception as e:
                    await interaction.response.send_message(
                        "Internal Bot ERROR", ephemeral=True
                    )
                    print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="TIME", row=1, style=discord.ButtonStyle.primary, emoji="⏰"
    )
    async def sort_by_time(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Sort by time'")
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            if self.sorted_by != SortedByEnum.VOICE:
                self.sorted_by = SortedByEnum.VOICE
                leaderboard_text = self._getLeaderBoard(page, SortedByEnum.VOICE)
                try:
                    await message.edit(content=leaderboard_text, view=self)
                except Exception as e:
                    await interaction.response.send_message(
                        "Internal Bot ERROR", ephemeral=True
                    )
                    print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="TEXT", row=1, style=discord.ButtonStyle.primary, emoji="💌"
    )
    async def sort_by_messages(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Sort by Messages'")
        message = interaction.message
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            if self.sorted_by != SortedByEnum.MESSAGES:
                self.sorted_by = SortedByEnum.MESSAGES
                leaderboard_text = self._getLeaderBoard(page, SortedByEnum.MESSAGES)
                try:
                    await message.edit(content=leaderboard_text, view=self)
                except Exception as e:
                    await interaction.response.send_message(
                        "Internal Bot ERROR", ephemeral=True
                    )
                    print(e)
        else:
            print("Error: Leaderboard button should have have a message")
        await interaction.response.defer(ephemeral=False)

    def _getLeaderBoard(self, page: int, sortBy: SortedByEnum) -> str:
        if self.timeFrame:
            return self._getTempLeaderBoard(page, sortBy)
        else:
            return self._getLeaderBoard(page, sortBy)

    def _getTotalLeaderBoard(self, page: int, sortBy: SortedByEnum) -> str:
        leaderboard_text = self.utils.getLeaderboardPageBy(page, sortBy.value)
        return leaderboard_text

    def _getTempLeaderBoard(self, page: int, sortByEnum: SortedByEnum) -> str:
        if sortByEnum == SortedByEnum.XP:
            sortBy = SortBy.VOICE_TEXT
        elif sortByEnum == SortedByEnum.VOICE:
            sortBy = SortBy.VOICE
        elif sortByEnum == SortedByEnum.MESSAGES:
            sortBy = SortBy.TEXTCOUNT
        else:
            sortBy = SortBy.NULL
        leaderboard_text = self.utils.getTempLeaderboardPageBy(page, sortBy, self.timeFrame)
        return leaderboard_text
