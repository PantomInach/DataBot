import discord
from discord.ui import Button

from datahandler.poll import Poll

POLL_EMOJIS = ("1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣")


class PollView(discord.ui.View):
    """
    Handles the buttons on a poll.

    Note that after a bot restart the polls need to be reopened.
    """

    def __init__(self, button_amount: int, poll: Poll, pollID: int):
        self.button_amount: int = button_amount
        self.poll: Poll = poll
        self.pollID: int = pollID
        super().__init__(timeout=None)
        for i in range(button_amount):
            self.add_item(self._create_button(i))

    def _create_button(self, vote_for_option: int) -> Button:
        button = VoteForButton(
            vote_for_option,
            self.poll,
            self.pollID,
            style=discord.ButtonStyle.primary,
            emoji=POLL_EMOJIS[vote_for_option],
        )
        return button


class VoteForButton(Button):
    def __init__(self, option: int, poll: Poll, pollID: int, *args, **kwargs):
        self.option = option
        self.poll = poll
        self.pollID = pollID
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await self._vote_for_option(interaction.user, self.option, interaction.message)
        option_text = self.poll.getOptionByNumber(self.pollID, self.option + 1)
        await interaction.response.send_message(
            f"You voted for option {self.option + 1}: '{option_text}'.",
            ephemeral=True,
            delete_after=60,
        )

    async def _vote_for_option(self, user, option, message):
        pollID = int(str(message.content)[6:10])
        optionName = self.poll.getOptionByNumber(pollID, option + 1)
        self.poll.addUserVote(pollID, user.id, optionName)
        await message.edit(content=f"{self.poll.pollString(pollID)}")
