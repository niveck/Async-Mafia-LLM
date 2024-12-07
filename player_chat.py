# TODO maybe use the portalocker library to prevent permission errors - read about it and whether it waits when file is locked or just skips
from game_constants import *  # incl. argparse, time, Path (from pathlib), colored (from termcolor)
from game_status_checks import is_game_over, is_time_to_vote, all_players_joined, get_is_mafia


def welcome_player(game_dir):
    print(colored(WELCOME_MESSAGE + "\n", MANAGER_COLOR))
    print(colored(RULES_OF_THE_GAME, MANAGER_COLOR))
    real_names_to_codenames_str = (game_dir / REAL_NAMES_FILE).read_text().splitlines()
    real_names_to_codenames = dict([real_to_code.split(REAL_NAME_CODENAME_DELIMITER)
                                    for real_to_code in real_names_to_codenames_str])
    real_name = get_player_name_from_user(real_names_to_codenames.keys(), GET_USER_NAME_MESSAGE)
    name = real_names_to_codenames[real_name]
    print(colored(CODE_NAME_REVELATION_MESSAGE_FORMAT.format(real_name), MANAGER_COLOR))
    print(colored(name, MANAGER_COLOR, attrs=["bold"]))  # TODO make a different color for more bolding
    is_mafia = get_is_mafia(name, game_dir)
    role = get_role_string(is_mafia)
    role_color = NIGHTTIME_COLOR if is_mafia else DAYTIME_COLOR
    print(colored(ROLE_REVELATION_MESSAGE, MANAGER_COLOR))
    print(colored(role, role_color))
    (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).write_text(JOINED)
    print(colored(WAITING_FOR_ALL_PLAYERS_TO_JOIN_MESSAGE, MANAGER_COLOR))
    while not all_players_joined(game_dir):
        continue
    # The game manager automatically posts a message that will be printed when the game starts
    return name, is_mafia  # name is used only in the joint read-and-write interface (with threads)


def display_lines_from_file(file_name, num_read_lines, display_color):
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    if len(lines) > 0:  # TODO if print() is deleted then remove this if!
        print()  # prevents the messages from being printed in the same line as the middle of input  # TODO validate it's not needed and delete if so
        for line in lines:
            print(colored(line.strip(), display_color))
    return len(lines)


def ask_player_to_vote():
    print(colored(VOTE_INSTRUCTION_MESSAGE, MANAGER_COLOR))


def read_game_text_loop(is_mafia, game_dir):
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
        if is_time_to_vote(game_dir):
            ask_player_to_vote()
            while is_time_to_vote(game_dir):
                continue  # wait for voting time to end when all players have voted


def game_over_message(game_dir):
    who_wins = (game_dir / WHO_WINS_FILE).read_text().strip()
    print(colored(who_wins, MANAGER_COLOR))
    mafia_names = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()  # removes the "\n"
    print(colored(MAFIA_REVELATION_MESSAGE, MANAGER_COLOR),
          colored(", ".join(mafia_names), MANAGER_COLOR, attrs=["bold"]))


def main():
    game_dir = get_game_dir_from_argv()
    _, is_mafia = welcome_player(game_dir)
    read_game_text_loop(is_mafia, game_dir)
    game_over_message(game_dir)


if __name__ == '__main__':
    main()
