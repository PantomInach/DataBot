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
owner_id: int = 0

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

"""
Roles Board
"""
roles_board_enabled: bool = True
roles_board_config_folder_path: str = "databot/roles_boards"

"""
XP System
"""
xp_system_enabled: bool = True
xp_database_path: str = "databot/data/xp.sqlite"
temp_xp_database_path: str = "databot/data/temp_xp.sqlite"

xp_cooldown: float = 60.0
xp_per_min: float = 0.5
# How much xp extra xp a user should get for having his cam on or is streaming.
xp_extra_factor: float = 1
xp_commit_interval: int = 120
