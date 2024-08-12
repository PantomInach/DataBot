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
# Specify for which level which role should be given. Each entry in the list must be a tuple
# consisting of the level, at which the role should be given, and the role id.
xp_roles_for_level: list[(int, int)] = []
xp_text_min: int = 15
xp_text_max: int = 25
xp_long_text_min: int = 20
xp_long_text_max: int = 40
xp_long_message_len: int = 150
xp_per_vote: int = 25

temp_xp_max_days: int = 60

leaderboard_member_per_page: int = 10

"""
Commands Channel Configurations

Specifies in which channel certain commands are allowed to be executed.
"""
top_channel: list[int | str] = []
level_channel: list[int | str] = []
