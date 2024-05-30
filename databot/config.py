"""
Config file containing all options for the bot.
"""

"""
Logging
"""
log_file: str = "databot.log"


"""
General config
"""
token: str = ""
command_prefix: str = "+"
guild_id: int = 0

"""
Quotes
"""
quotes_enabled: bool = True
quotes_allowed_channel: tuple[int | str] | None = None
quotes_allow_in_dms: bool = True

"""
Dynamic Channel
"""
dynamic_channel_enabled: bool = True
