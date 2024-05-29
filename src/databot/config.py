"""
Config file containing all options for the bot.
"""

"""
Logging
"""
log_file: str = "databot.log"

token: str = ""
command_prefix: str = "+"

"""
Quotes
"""
quotes_enabled: bool = True
quotes_allowed_channel: tuple[int | str] | None = None
quotes_allow_in_dms: bool = True
