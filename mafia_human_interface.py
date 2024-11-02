import os
from pathlib import Path
from termcolor import colored
from threading import Thread  # TODO divide this file so there will be one version for multi threading and one version for separate windows
from game_constants import *
from game_status_checks import is_nighttime, is_game_over, is_voted_out

# output colors
MANAGER_COLOR = "green"
DAYTIME_COLOR = "light_blue"
NIGHTTIME_COLOR = "red"
# user messages
WELCOME_MESSAGE = "Welcome to the game of Mafia!"
GET_USER_NAME_MESSAGE = "Who are you? Enter the name's number: "
VOTE_FLAG = "VOTE"
GET_INPUT_MESSAGE = f"Enter a message to public chat, or '{VOTE_FLAG}' to cast a vote: "
GET_VOTED_NAME_MESSAGE = "Make your vote! You can change your vote until elimination is done." \
                         "Enter your vote's number: "
ROLE_REVELATION_MESSAGE = "Your role in the game is:"
YOU_CANT_WRITE_MESSAGE = "You were voted out and can no longer write messages."


# global variable
input(colored("Press enter only after the main game code started running...",  # to get latest dir
              MANAGER_COLOR))  # TODO maybe change it to get an argument for the game's key
game_dir = max(Path(DIRS_PREFIX).glob("*"), key=os.path.getmtime)  # latest modified dir


def get_player_names_by_id(player_names_file):
    player_names = (game_dir / player_names_file).read_text().splitlines()
    return {f"{i}": name for i, name in enumerate(player_names) if name}


def get_player_name_from_user(optional_player_names_file, input_message):
    player_names_by_id = get_player_names_by_id(optional_player_names_file)
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
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    if len(lines) > 0:  # TODO if print() is deleted then remove this if!
        print()  # prevents the messages from being printed in the same line as the middle of input  # TODO validate it's not needed and delete if so
        for line in lines:
            print(colored(line.strip(), display_color))  # TODO maybe need display_line func for special format?
    return len(lines)


def read_game_text(is_mafia):
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


def collect_vote(name):
    voted_name = get_player_name_from_user(REMAINING_PLAYERS_FILE, GET_VOTED_NAME_MESSAGE)
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game(name, is_mafia):
    while not is_game_over(game_dir):
        if is_voted_out(name, game_dir):
            print(colored(YOU_CANT_WRITE_MESSAGE, MANAGER_COLOR))
            break  # can't write or vote anymore (but can still read the game's content)
        if not is_mafia and is_nighttime(game_dir):
            continue  # only mafia can communicate during nighttime
        user_input = input(colored(GET_INPUT_MESSAGE, MANAGER_COLOR)).strip()
        if user_input.lower() == VOTE_FLAG.lower():  # lower for robustness, even though it's caps
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


def welcome_player():
    print(colored(WELCOME_MESSAGE, MANAGER_COLOR))
    print(colored(RULES_OF_THE_GAME, MANAGER_COLOR))
    name = get_player_name_from_user(PLAYER_NAMES_FILE, GET_USER_NAME_MESSAGE)
    is_mafia = get_is_mafia(name)
    role = get_role_string(is_mafia)
    role_color = NIGHTTIME_COLOR if is_mafia else DAYTIME_COLOR
    print(colored(ROLE_REVELATION_MESSAGE, MANAGER_COLOR), colored(role, role_color))
    return name, is_mafia


def game_over_message():
    who_wins = (game_dir / WHO_WINS_FILE).read_text().strip()
    print(colored(who_wins, MANAGER_COLOR))
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    mafia_revelation = f"Mafia members were: " + ",".join(mafia_names)
    print(colored(mafia_revelation, MANAGER_COLOR))


def main():
    name, is_mafia = welcome_player()
    game_read_and_write_loop(name, is_mafia)
    game_over_message()


if __name__ == '__main__':
    main()
