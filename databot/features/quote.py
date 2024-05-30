import aiohttp
import logging

from discord import Embed, channel
from discord.ext import commands

from databot.command_checks import in_channel
from databot.config import quotes_enabled, quotes_allow_in_dms, quotes_allowed_channel

log = logging.getLogger(__name__)

URL = "https://inspirobot.me/api?generate=true"


class QuotesCogs(commands.Cog, name="Quote Commands"):
    """
    Commands to generate a random quote.
    """

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name="quote", brief="Sends an unique inspirational quote.")
    @in_channel(quotes_allowed_channel, quotes_allow_in_dms)
    async def get_quote(self, ctx: commands.Context):
        """
        Sent a AI generated inspirational quote via 'quote'.
        These quotes are randomly from 'inspirobot.me'.
        """
        if isinstance(ctx.channel, channel.DMChannel):
            log.info("User %s invoked 'quote' in channel 'DMChannel'", ctx.author.name)
        else:
            log.info("User %s invoked 'quote' in channel %s", ctx.author.name, ctx.channel.name)

        url = await get_picture_url()
        # Create Embeded
        embed = Embed(color=12008408)
        embed.set_image(url=url)
        embed.set_footer(text=url)
        await ctx.send(content=ctx.author.mention, embed=embed)
        await ctx.message.delete()


async def get_picture_url():
    """
    Opens inspirobot site to fetch URL for a random new quote url.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            return await response.text()


async def setup(bot: commands.Bot):
    if quotes_enabled:
        log.info("Loaded 'QuotesCogs'.")
        await bot.add_cog(QuotesCogs(bot))
    else:
        log.info("Did not Loaded 'QuotesCogs' since they are not enabled.")
