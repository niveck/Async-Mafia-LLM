import time


# files that host writes to and players read from
DIRS_PREFIX = "./games"
PLAYER_NAMES_FILE = "player_names.txt"
REMAINING_PLAYERS_FILE = "remaining_players.txt"
MAFIA_NAMES_FILE = "mafia_names.txt"
PHASE_STATUS_FILE = "phase_status.txt"
WHO_WINS_FILE = "who_wins.txt"
PUBLIC_MANAGER_CHAT_FILE = "public_manager_chat.txt"
PUBLIC_DAYTIME_CHAT_FILE = "public_daytime_chat.txt"
PUBLIC_NIGHTTIME_CHAT_FILE = "public_nighttime_chat.txt"
PERSONAL_STATUS_FILE_FORMAT = "{}_status.txt"
# files that hosts read from and players write to
PERSONAL_CHAT_FILE_FORMAT = "{}_chat.txt"
PERSONAL_VOTE_FILE_FORMAT = "{}_vote.txt"
# constant strings for info files
NIGHTTIME = "NIGHTTIME"
DAYTIME = "DAYTIME"
VOTED_OUT = "VOTED_OUT"
MAFIA_ROLE = "mafia"
BYSTANDER_ROLE = "bystander"
MAFIA_WINS_MESSAGE = "Mafia wins!"
BYSTANDERS_WIN_MESSAGE = "Bystanders win!"
GAME_MANAGER_NAME = "Game-Manager"
RULES_OF_THE_GAME = "You are playing the game of Mafia. In this game each player is assigned a " \
                    "role secretly, either mafia or bystander. Every round a player is " \
                    "eliminated by the mafia during Nighttime, then during Daytime all remaining " \
                    "players discuss together who they think the mafia players are and vote out " \
                    "another player. The mafia's goal is to outnumber the bystanders, and the " \
                    "bystanders' goal it to vote out all real mafia."
# formats for saving texts
TIME_FORMAT_FOR_TIMESTAMP = "%H:%M:%S"
MESSAGE_FORMAT = "[{timestamp}] {name}: {message}"
VOTING_MESSAGE_FORMAT = "{} voted for {}"
VOTED_OUT_MESSAGE_FORMAT = "{} was voted out. Their role was {}"
# game constants
NIGHTTIME_TIME_LIMIT_MINUTES = 1  # 2
NIGHTTIME_TIME_LIMIT_SECONDS = int(NIGHTTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_TIME_LIMIT_MINUTES = 3  # 5
DAYTIME_TIME_LIMIT_SECONDS = int(DAYTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_BEGINNING_MESSAGE = f"Now it's Daytime for {DAYTIME_TIME_LIMIT_MINUTES} minutes, " \
                            f"everyone can communicate and see messages and votes."
NIGHTTIME_BEGINNING_MESSAGE = f"Now it's Nighttime for {NIGHTTIME_TIME_LIMIT_MINUTES} minutes, " \
                              f"only mafia can communicate and see messages and votes."
# LLM messages and constants
LLM_VOTE_KEYWORD = "VOTE"
LLM_VOTING_PATTERN = rf"{LLM_VOTE_KEYWORD} (\w[ \w]*)"  # at least one letter and before spaces
DEFAULT_PASS_TURN_TOKEN = "<wait>"
DEFAULT_USE_TURN_TOKEN = "<speak>"


def format_message(name, message):
    timestamp = time.strftime(TIME_FORMAT_FOR_TIMESTAMP)
    return MESSAGE_FORMAT.format(timestamp=timestamp, name=name, message=message) + "\n"


def get_role_string(is_mafia):
    return MAFIA_ROLE if is_mafia else BYSTANDER_ROLE
