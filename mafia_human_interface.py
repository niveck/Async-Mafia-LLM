from termcolor import colored
from threading import Thread  # TODO divide this file so there will be one version for multi threading and one version for separate windows
from game_constants import *  # including: argparse, time, Path (from pathlib)
from game_status_checks import is_nighttime, is_game_over, is_voted_out, check_for_time_to_vote

# output colors
MANAGER_COLOR = "green"
DAYTIME_COLOR = "light_blue"
NIGHTTIME_COLOR = "red"
# user messages
WELCOME_MESSAGE = "Welcome to the game of Mafia!"
GET_USER_NAME_MESSAGE = "Who are you? Enter the name's number: "
VOTE_FLAG = "VOTE"
# GET_INPUT_MESSAGE = f"Enter a message to public chat, or '{VOTE_FLAG}' to cast a vote: "  # TODO make sure no need to use anymore and can be removed
GET_CHAT_INPUT_MESSAGE = f"Enter a message to the public chat: "
VOTE_INSTRUCTION_MESSAGE = f"You have {VOTING_TIME_LIMIT_SECONDS} seconds to cast your vote!\n" \
                           f"Enter '{VOTE_FLAG}' as your input to vote..."
GET_VOTED_NAME_MESSAGE = "Make your vote! You can change your vote until elimination is done." \
                         "Enter your vote's number: "
CODE_NAME_REVELATION_MESSAGE_FORMAT = "\nHi {0}! Your name for this game will be:"
ROLE_REVELATION_MESSAGE = "\nYour role in the game is:"
MAFIA_REVELATION_MESSAGE = "Mafia members were:"
YOU_CANT_WRITE_MESSAGE = "You were voted out and can no longer write messages."
WAITING_FOR_ALL_PLAYERS_TO_JOIN_MESSAGE = "Waiting for all players to join to start the game..."


# global variable
game_dir = Path()  # will be updated in welcome_player
is_time_to_vote = False


def get_player_names_by_id(player_names):
    return {f"{i}": name for i, name in enumerate(player_names) if name}


def get_player_name_from_user(optional_player_names, input_message):
    player_names_by_id = get_player_names_by_id(optional_player_names)
    name_id = ""
    enumerated_names = ",   ".join([f"{i}: {name}" for i, name in player_names_by_id.items()])
    while name_id not in player_names_by_id:
        name_id = input(colored(f"{input_message}\n{enumerated_names} ",
                                MANAGER_COLOR))
    name = player_names_by_id[name_id]
    return name


def get_is_mafia(name):
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    return name in mafia_names


def display_lines_from_file(file_name, num_read_lines, display_color):
    global is_time_to_vote
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    if len(lines) > 0:  # TODO if print() is deleted then remove this if!
        print()  # prevents the messages from being printed in the same line as the middle of input  # TODO validate it's not needed and delete if so
        for line in lines:
            print(colored(line.strip(), display_color))  # TODO maybe need display_line func for special format?
            if check_for_time_to_vote(line):
                is_time_to_vote = True
    return len(lines)


def ask_player_to_vote():
    print(colored(VOTE_INSTRUCTION_MESSAGE, MANAGER_COLOR))


def read_game_text(is_mafia):
    global is_time_to_vote
    num_read_lines_manager = num_read_lines_daytime = num_read_lines_nighttime = 0
    while not is_game_over(game_dir):
        num_read_lines_manager += display_lines_from_file(
            PUBLIC_MANAGER_CHAT_FILE, num_read_lines_manager, MANAGER_COLOR)
        # only current phase file will have new messages, so no need to run expensive is_nighttime()
        num_read_lines_daytime += display_lines_from_file(
            PUBLIC_DAYTIME_CHAT_FILE, num_read_lines_daytime, DAYTIME_COLOR)
        if is_mafia:  # only mafia can see what happens during nighttime
            num_read_lines_nighttime += display_lines_from_file(
                PUBLIC_NIGHTTIME_CHAT_FILE, num_read_lines_nighttime, NIGHTTIME_COLOR)
        if is_time_to_vote:
            ask_player_to_vote()
            is_time_to_vote = False


def collect_vote(name):
    remaining_player_names = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    voted_name = get_player_name_from_user(remaining_player_names, GET_VOTED_NAME_MESSAGE)
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game(name, is_mafia):
    while not is_game_over(game_dir):
        if is_voted_out(name, game_dir):
            print(colored(YOU_CANT_WRITE_MESSAGE, MANAGER_COLOR))
            break  # can't write or vote anymore (but can still read the game's content)
        if not is_mafia and is_nighttime(game_dir):
            continue  # only mafia can communicate during nighttime
        user_input = input(colored(GET_CHAT_INPUT_MESSAGE, MANAGER_COLOR)).strip()
        if user_input == VOTE_FLAG:  # TODO maybe add a check that it is time to vote?... when it is divided to different terminal
            collect_vote(name)
        else:
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
                f.write(format_message(name, user_input))


def game_read_and_write_loop(name, is_mafia):
    write_thread = Thread(target=write_text_to_game, args=(name, is_mafia))
    # daemon: writing in the background, so it can stop when eliminated and still allow reading
    write_thread.daemon = True
    write_thread.start()
    read_game_text(is_mafia)


def all_players_joined():
    # game is started by manager after all players joined, and then the file will not be empty
    return bool((game_dir / GAME_START_TIME_FILE).read_text())


def welcome_player():
    global game_dir
    game_dir = get_game_dir_from_argv()
    print(colored(WELCOME_MESSAGE, MANAGER_COLOR))
    print(colored(RULES_OF_THE_GAME, MANAGER_COLOR))
    real_names_to_codenames_str = (game_dir / REAL_NAMES_FILE).read_text().splitlines()
    real_names_to_codenames = dict([real_to_code.split(REAL_NAME_CODENAME_DELIMITER)
                                    for real_to_code in real_names_to_codenames_str])
    real_name = get_player_name_from_user(real_names_to_codenames.keys(), GET_USER_NAME_MESSAGE)
    name = real_names_to_codenames[real_name]
    print(colored(CODE_NAME_REVELATION_MESSAGE_FORMAT.format(real_name), MANAGER_COLOR),
          colored(name, MANAGER_COLOR, attrs=["bold"]))
    is_mafia = get_is_mafia(name)
    role = get_role_string(is_mafia)
    role_color = NIGHTTIME_COLOR if is_mafia else DAYTIME_COLOR
    print(colored(ROLE_REVELATION_MESSAGE, MANAGER_COLOR), colored(role, role_color))
    (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).write_text(JOINED)
    print(colored(WAITING_FOR_ALL_PLAYERS_TO_JOIN_MESSAGE, MANAGER_COLOR))
    while not all_players_joined():
        pass
    # The game manager automatically posts a message that will be printed when the game starts
    return name, is_mafia


def game_over_message():
    who_wins = (game_dir / WHO_WINS_FILE).read_text().strip()
    print(colored(who_wins, MANAGER_COLOR))
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    print(colored(MAFIA_REVELATION_MESSAGE, MANAGER_COLOR),
          colored(", ".join(mafia_names), MANAGER_COLOR, attrs=["bold"]))


def main():
    name, is_mafia = welcome_player()
    game_read_and_write_loop(name, is_mafia)
    game_over_message()


if __name__ == '__main__':
    main()
