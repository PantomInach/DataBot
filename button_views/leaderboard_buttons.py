import discord
from enum import Enum


class SortedByEnum(Enum):
    XP = 0
    VOICE = 1
    MESSAGES = 2


class LeaderboardButtons(discord.ui.View):
    def __init__(self, utils):
        self.sorted_by = SortedByEnum.XP
        self.utils = utils
        super().__init__()

    # @discord.ui.button(label="Page:", row=0, disabled=True, style=discord.ButtonStyle.secondary)
    # async def page_spacer(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="First", row=0, style=discord.ButtonStyle.primary, emoji="⏫"
    )
    async def go_to_page_one(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        print("Invoking leaderboard button 'Go to page one'")
        message = interaction.message
        print(message)
        if message:
            _, page = self.utils.getMessageState(message, view=self)
            print("First", page)
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
        label="Previous", row=0, style=discord.ButtonStyle.primary, emoji="⬅️"
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
        label="Next", row=0, style=discord.ButtonStyle.primary, emoji="➡️"
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
        print("Ending next")
        await interaction.response.defer(ephemeral=False)

    # @discord.ui.button(label="Sort by", row=1, disabled=True, style=discord.ButtonStyle.secondary)
    # async def sort_by_spacer(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="Exp", row=1, style=discord.ButtonStyle.primary, emoji="🌟"
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
        label="Time", row=1, style=discord.ButtonStyle.primary, emoji="⏰"
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
        print("Ending time")
        await interaction.response.defer(ephemeral=False)

    @discord.ui.button(
        label="Messages", row=1, style=discord.ButtonStyle.primary, emoji="💌"
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
        print("Ending message")
        await interaction.response.defer(ephemeral=False)

    def _getLeaderBoard(self, page: int, sortBy: SortedByEnum) -> str:
        # print("GetLeaderBoard:", sortBy, sortBy.value)
        leaderboard_text = self.utils.getLeaderboardPageBy(page, sortBy.value)
        # print("GetLeaderBoard:", leaderboard_text)
        return leaderboard_text
