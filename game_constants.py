import time


# new game preparation constants  # TODO maybe change all ".." paths to absolute/from root?
DEFAULT_GAME_CONFIG = "configurations/1llm2humans.json"  # TODO choose a better config
GAME_ID_NUM_DIGITS = 5
NOTES_FILE = "notes.txt"  # for our use, post-game
# TODO: remember to add a notes.txt file for each game so I can add it later!
# files that host writes to and players read from
DIRS_PREFIX = "./games"  # TODO maybe change to absolute!
GAME_CONFIG_FILE = "config.json"
PLAYER_NAMES_FILE = "player_names.txt"
REMAINING_PLAYERS_FILE = "remaining_players.txt"
MAFIA_NAMES_FILE = "mafia_names.txt"
PHASE_STATUS_FILE = "phase_status.txt"
WHO_WINS_FILE = "who_wins.txt"
GAME_START_TIME_FILE = "game_start_time.txt"
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
RULES_OF_THE_GAME = "In this game each player is assigned a role secretly, either mafia or " \
                    "bystander. Every round starts with Nighttime phase, where only mafia " \
                    "players interact and vote to decide which bystander player they want to " \
                    "eliminate (bystanders aren't exposed to the mafia identities or " \
                    "interaction). Then it moves to Daytime phase, where all remaining players " \
                    "discuss together who they think the mafia players are and vote out another " \
                    "player. The mafia's goal is to outnumber the bystanders, and the " \
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
LLM_VOTING_PATTERN = rf"{LLM_VOTE_KEYWORD} (\w[ \w]*)"  # at least one letter and before spaces  # TODO no need anymore
DEFAULT_PASS_TURN_TOKEN = "<wait>"
DEFAULT_USE_TURN_TOKEN = "<send>"
GENERAL_SYSTEM_INFO = f"You are a bot player in an online version of the party game Mafia.\n" \
                      f"The rules of the game: {RULES_OF_THE_GAME}"
# new configuration preparation constants
PLAYERS_KEY_IN_CONFIG = "players"
DEFAULT_CONFIG_DIR = "./configurations"
DEFAULT_NUM_MAFIA = 2
MINIMUM_NUM_PLAYERS_FOR_ONE_MAFIA = 5
MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA = 7
DEFAULT_NUM_PLAYERS = MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA
WARNING_LIMIT_NUM_MAFIA = 3
# I've tried using mainly unisex names...
OPTIONAL_CODE_NAMES = ["Addison", "Adrian", "Alex", "Angel", "Ari", "Ariel", "Ashton", "Avery",
                       "Bailey",  "Blake", "Brook", "Cameron", "Casey", "Charlie", "Dakota", "Drew",
                       "Dylan", "Eden", "Elliot", "Emerson", "Finley", "Frankie", "Gray", "Harley",
                       "Harper", "Hayden", "Jamie", "Jordan", "Kai", "Kennedy", "Lee", "Lennon",
                       "Logan", "Mickey", "Morgan", "Parker", "Peyton", "Quinn", "Ray", "Reese",
                       "Remi", "Riley", "River", "Robin", "Rowan", "Sage", "Sam", "Sidney",
                       "Skylar", "Stevie", "Sutton", "Terry", "Tyler", "Whitney", "Winter", "Ziggy"]


def get_current_timestamp():
    return time.strftime(TIME_FORMAT_FOR_TIMESTAMP)


def format_message(name, message):
    timestamp = get_current_timestamp()
    return MESSAGE_FORMAT.format(timestamp=timestamp, name=name, message=message) + "\n"


def get_role_string(is_mafia):
    return MAFIA_ROLE if is_mafia else BYSTANDER_ROLE
