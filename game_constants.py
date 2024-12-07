import argparse
import random
import time
from pathlib import Path
from termcolor import colored


# new game preparation constants
# DEFAULT_GAME_CONFIG = "configurations/minimalist_game_with_llm.json"
DEFAULT_GAME_CONFIG = "configurations/minimalist_game_no_llm.json"
GAME_ID_NUM_DIGITS = 4
NOTES_FILE = "notes.txt"  # for our use, post-game

# files that host writes to and players read from
DIRS_PREFIX = "./games"  # TODO maybe change to absolute!
GAME_CONFIG_FILE = "config.json"
PLAYER_NAMES_FILE = "player_names.txt"
REMAINING_PLAYERS_FILE = "remaining_players.txt"
MAFIA_NAMES_FILE = "mafia_names.txt"
REAL_NAMES_FILE = "real_names.txt"  # mapping of real names to code names
PHASE_STATUS_FILE = "phase_status.txt"
WHO_WINS_FILE = "who_wins.txt"
GAME_START_TIME_FILE = "game_start_time.txt"
PUBLIC_MANAGER_CHAT_FILE = "public_manager_chat.txt"
PUBLIC_DAYTIME_CHAT_FILE = "public_daytime_chat.txt"
PUBLIC_NIGHTTIME_CHAT_FILE = "public_nighttime_chat.txt"
# file that is initial used for players to write "joined", and then for host to write "eliminated"
PERSONAL_STATUS_FILE_FORMAT = "{}_status.txt"
# files that hosts read from and players write to
PERSONAL_CHAT_FILE_FORMAT = "{}_chat.txt"
PERSONAL_VOTE_FILE_FORMAT = "{}_vote.txt"
LLM_LOG_FILE_FORMAT = "{}_log.txt"

# constant strings for info files
NIGHTTIME = "Nighttime"
DAYTIME = "Daytime"
VOTING_TIME = "Voting"
NIGHTTIME_VOTING_TIME = NIGHTTIME + "_" + VOTING_TIME  # keeps the is_nighttime function mechanism
DAYTIME_VOTING_TIME = DAYTIME + "_" + VOTING_TIME
JOINED = "JOINED"
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
REAL_NAME_CODENAME_DELIMITER = ": "  # <real name>: <codename>

# game constants
NIGHTTIME_TIME_LIMIT_MINUTES = 1
NIGHTTIME_TIME_LIMIT_SECONDS = int(NIGHTTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_TIME_LIMIT_MINUTES = 1  # 3  # TODO return to 3! TODO: actually check times in original paper
DAYTIME_TIME_LIMIT_SECONDS = int(DAYTIME_TIME_LIMIT_MINUTES * 60)
DAYTIME_BEGINNING_MESSAGE = f"Now it's Daytime for {DAYTIME_TIME_LIMIT_MINUTES} minutes, " \
                            f"everyone can communicate and see messages and votes."
NIGHTTIME_BEGINNING_MESSAGE = f"Now it's Nighttime for {NIGHTTIME_TIME_LIMIT_MINUTES} minutes, " \
                              f"only mafia can communicate and see messages and votes."
VOTING_TIME_MESSAGE_FORMAT = "{} has ended, now it's time to vote! " \
                             "Waiting for all players to vote..."
CUTTING_TO_VOTE_MESSAGE = "There is only one mafia member left, so no need for discussion" \
                          " - cutting straight to voting!"
DAYTIME_VOTING_TIME_MESSAGE = VOTING_TIME_MESSAGE_FORMAT.format(DAYTIME)
NIGHTTIME_VOTING_TIME_MESSAGE = VOTING_TIME_MESSAGE_FORMAT.format(NIGHTTIME)

# new configuration preparation constants
PLAYERS_KEY_IN_CONFIG = "players"
DEFAULT_CONFIG_DIR = "./configurations"
DEFAULT_NUM_MAFIA = 2
MINIMUM_NUM_PLAYERS_FOR_ONE_MAFIA = 5
MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA = 7
DEFAULT_NUM_PLAYERS = MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA
WARNING_LIMIT_NUM_MAFIA = 3
OPTIONAL_CODE_NAMES = [  # I've tried using mainly unisex names, as suggest by Claud + additions
    "Addison", "Adrian", "Alex", "Angel", "Ari", "Ariel", "Ashton", "Avery", "Bailey", "Blake",
    "Brook", "Cameron", "Casey", "Charlie", "Dakota", "Drew", "Dylan", "Eden", "Elliot", "Emerson",
    "Finley", "Frankie", "Gray", "Harley", "Harper", "Hayden", "Jackie", "Jamie", "Jordan", "Kai",
    "Kennedy", "Lee", "Lennon", "Logan", "Mickey", "Morgan", "Noah", "Parker", "Peyton", "Quinn",
    "Ray", "Reese", "Remi", "Riley", "River", "Robin", "Ronny", "Rowan", "Sage", "Sam", "Sidney",
    "Skylar", "Stevie", "Sutton", "Terry", "Tyler", "Whitney", "Winter", "Ziggy"]
random.shuffle(OPTIONAL_CODE_NAMES)  # without it some names are sampled too often...

# human player interface constants
MANAGER_COLOR = "green"
DAYTIME_COLOR = "light_blue"
NIGHTTIME_COLOR = "red"
WELCOME_MESSAGE = "Welcome to the game of Mafia!"
GET_USER_NAME_MESSAGE = "Who are you? Enter the name's number:"
VOTE_FLAG = "VOTE"
GET_CHAT_INPUT_MESSAGE = f"Enter a message to the public chat: "
VOTE_INSTRUCTION_MESSAGE = f"We are now waiting for everyone to cast their vote!\n" \
                           f"Enter '{VOTE_FLAG}' as your input to vote..."
GET_VOTED_NAME_MESSAGE_FORMAT = "It's time to make your vote, {}!\nEnter your vote's number:"
CODE_NAME_REVELATION_MESSAGE_FORMAT = "\nHi {}! Your name for this game will be:"
ROLE_REVELATION_MESSAGE = "\nYour role in the game is:"
MAFIA_REVELATION_MESSAGE = "Mafia members were:"
YOU_CANT_WRITE_MESSAGE = "You were voted out and can no longer write messages."
WAITING_FOR_ALL_PLAYERS_TO_JOIN_MESSAGE = "Waiting for all players to join to start the game..."
WELCOME_INPUT_INTERFACE_MESSAGE = "This interface will only serve you to enter your messages and " \
                                  "votes.\nAll other game info, messages and chat will be " \
                                  "visible in the chat interface (run by `player_chat.py`)"
GET_CODE_NAME_FROM_USER_MESSAGE = "Enter the name you were given for this game " \
                                  "(in the chat interface) - choose the name's number:"
YOU_CAN_START_WRITING_MESSAGE = "You can now start writing messages to game!"


def get_current_timestamp():
    return time.strftime(TIME_FORMAT_FOR_TIMESTAMP)


def format_message(name, message):
    timestamp = get_current_timestamp()
    return MESSAGE_FORMAT.format(timestamp=timestamp, name=name, message=message) + "\n"


def get_role_string(is_mafia):
    return MAFIA_ROLE if is_mafia else BYSTANDER_ROLE


def get_game_dir_from_argv():
    parser = argparse.ArgumentParser()
    parser.add_argument("game_id", help=f"{GAME_ID_NUM_DIGITS}-digit game ID")
    args = parser.parse_args()
    game_dir = Path(DIRS_PREFIX) / args.game_id
    if not game_dir.exists():
        raise ValueError(f"The provided game ID {args.game_id} doesn't belong to a configured game")
    return game_dir


def get_player_names_by_id(player_names):
    return {f"{i}": name for i, name in enumerate(player_names) if name}


def get_player_name_from_user(optional_player_names, input_message, message_color=MANAGER_COLOR):
    player_names_by_id = get_player_names_by_id(optional_player_names)
    name_id = ""
    enumerated_names = ",   ".join([f"{i}: {name}" for i, name in player_names_by_id.items()])
    while name_id not in player_names_by_id:
        name_id = input(colored(f"{input_message}\n{enumerated_names}\n", message_color))
    name = player_names_by_id[name_id]
    return name
