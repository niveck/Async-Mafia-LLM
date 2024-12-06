# TODO maybe use the portalocker library to prevent permission errors - read about it and whether it waits when file is locked or just skips
from game_constants import *  # incl. argparse, time, Path (from pathlib), colored (from termcolor)
from game_status_checks import is_nighttime, is_game_over, is_voted_out, is_time_to_vote, \
    all_players_joined

# global variable
game_dir = Path()  # will be updated in get_name_and_role


def get_name_and_role():
    pass  # TODO!!!


def collect_vote(name):
    remaining_player_names = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    remaining_player_names.remove(name)  # players shouldn't vote for themselves  # TODO validate that there is no error in remove if someone that was voted our tries to vote
    voted_name = get_player_name_from_user(remaining_player_names,
                                           GET_VOTED_NAME_MESSAGE_FORMAT.format(name), MANAGER_COLOR)
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def write_text_to_game_loop(name, is_mafia):
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
            collect_vote(name)
            while is_time_to_vote(game_dir):
                continue  # wait for voting time to end when all players have voted
        elif not is_time_to_vote(game_dir):  # if it's time to vote then players can't chat
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(name), "a") as f:
                f.write(format_message(name, user_input))


def main():
    name, is_mafia = get_name_and_role()
    write_text_to_game_loop(name, is_mafia)


if __name__ == '__main__':
    main()
