from discord.ext import commands

from helpfunctions.utils import Utils
from datahandler.textban import Textban
from datahandler.configHandle import ConfigHandle
from datahandler.userHandle import UserHandle


def hasAnyRole(*items):
    """
    Type:	Decorator for functions with ctx object in args[1].

    param items:	Tuple of strings and/or integers wit Discord channel IDs or names.

    Check if a user has any of the roles in items.

    Only use for commands, which USE @commands.command
    commands.has_any_role() does not work in DM, since a user can't have roles.
    This one pulls the roles from the configured guild and makes the same check as
    commands.has_any_role().

    Function is not in decorators.py since the Helpfunction Object is needed.
    """

    def predicate(ctx):
        return Commandmodserver.utils.hasOneRole(ctx.author.id, [*items])

    return commands.check(predicate)


class Commandmodserver(commands.Cog, name="Server Mod Commands"):
    """
    Currently unused
    """

    utils = None

    def __init__(self, bot):
        super(Commandmodserver, self).__init__()
        self.bot = bot
        self.ch = ConfigHandle()
        self.tban = Textban()
        self.uh = UserHandle()
        self.utils = Utils(bot, ch=self.ch, uh=self.uh)
        Commandmodserver.utils = self.utils


async def setup(bot):
    await bot.add_cog(Commandmodserver(bot))
