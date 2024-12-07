# TODO maybe use the portalocker library to prevent permission errors - read about it and whether it waits when file is locked or just skips
from game_constants import *  # incl. random, Path (from pathlib), colored (from termcolor)
from game_status_checks import is_nighttime, is_game_over, is_voted_out, is_time_to_vote, \
    all_players_joined, get_is_mafia


def get_name_and_role(game_dir):
    print(colored(WELCOME_INPUT_INTERFACE_MESSAGE + "\n", MANAGER_COLOR))
    player_names = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    random.shuffle(player_names)
    name = get_player_name_from_user(player_names, GET_CODE_NAME_FROM_USER_MESSAGE)
    is_mafia = get_is_mafia(name, game_dir)
    print(colored(WAITING_FOR_ALL_PLAYERS_TO_JOIN_MESSAGE, MANAGER_COLOR))
    while not all_players_joined(game_dir):
        continue
    print(colored(YOU_CAN_START_WRITING_MESSAGE, MANAGER_COLOR))
    return name, is_mafia


def collect_vote(name, game_dir):
    remaining_player_names = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    remaining_player_names.remove(name)  # players shouldn't vote for themselves  # TODO validate that there is no error in remove if someone that was voted our tries to vote
    voted_name = get_player_name_from_user(remaining_player_names,
                                           GET_VOTED_NAME_MESSAGE_FORMAT.format(name))
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game_loop(name, is_mafia, game_dir):
    while not is_game_over(game_dir):
        if is_voted_out(name, game_dir):
            print(colored(YOU_CANT_WRITE_MESSAGE, MANAGER_COLOR))
            break  # can't write or vote anymore (but can still read the game's content)
        if not is_mafia and is_nighttime(game_dir):
            continue  # only mafia can communicate during nighttime
        user_input = input(colored(GET_CHAT_INPUT_MESSAGE, MANAGER_COLOR)).strip()
        if not user_input:
            continue
        elif user_input == VOTE_FLAG:
            collect_vote(name, game_dir)
            while is_time_to_vote(game_dir):
                continue  # wait for voting time to end when all players have voted
        elif not is_time_to_vote(game_dir):  # if it's time to vote then players can't chat
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
                f.write(format_message(name, user_input))


def main():
    game_dir = get_game_dir_from_argv()
    name, is_mafia = get_name_and_role(game_dir)
    write_text_to_game_loop(name, is_mafia, game_dir)


if __name__ == '__main__':
    main()
