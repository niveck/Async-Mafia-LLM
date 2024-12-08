import json
from game_constants import *  # incl. argparse, time, Path (from pathlib), colored (from termcolor)
from game_status_checks import is_nighttime, is_game_over, is_voted_out, is_time_to_vote, \
    all_players_joined
from llm_players.factory import llm_player_factory
from llm_players.llm_constants import GAME_DIR_KEY


OPERATOR_COLOR = "yellow"  # the person running this file is the "operator" of the model
LLM_PLAYER_LOADED_MESSAGE = "The LLM PLayer was loaded successfully, " \
                            "now waiting for all other players to join..."
ALL_PLAYERS_JOINED_MESSAGE = "All players have joined, now the game can start."
GAME_ENDED_MESSAGE = "Game has ended, without being voted out!"
GET_LLM_PLAYER_NAME_MESSAGE = "This game has multiple LLM players, which one you want to run now?"
ELIMINATED_MESSAGE = "This LLM player was eliminated from the game..."


# global variable
game_dir = Path()  # will be updated in get_llm_player


def get_llm_player():
    global game_dir
    game_dir = get_game_dir_from_argv()
    with open(game_dir / GAME_CONFIG_FILE) as f:
        config = json.load(f)
    llm_players_configs = [player for player in config[PLAYERS_KEY_IN_CONFIG] if player["is_llm"]]
    if not llm_players_configs:
        raise ValueError("No LLM player configured in this game")
    elif len(llm_players_configs) == 1:
        player_config = llm_players_configs[0]
    else:
        player_name = get_player_name_from_user([player["name"] for player in llm_players_configs],
                                                GET_LLM_PLAYER_NAME_MESSAGE, OPERATOR_COLOR)
        player_config = [player for player in llm_players_configs
                         if player["name"] == player_name][0]
    player_config[GAME_DIR_KEY] = game_dir  # TODO maybe GAME_DIR_KEY is unnecessary like "name"
    llm_player = llm_player_factory(player_config)
    (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(llm_player.name)).write_text(JOINED)
    return llm_player


def read_messages_from_file(message_history, file_name, num_read_lines):
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    message_history.extend(lines)
    return len(lines)


def wait_writing_time(player, message):
    if player.num_words_per_second_to_wait > 0:
        num_words = len(message.split())
        time.sleep(num_words // player.num_words_per_second_to_wait)


def eliminate(player):
    print(colored(ELIMINATED_MESSAGE, OPERATOR_COLOR))
    # TODO maybe log how much time it lasted in the game, how many players were left when it was voted out and maybe how many time it was voted for


def get_vote_from_llm(player, message_history):
    candidate_vote_names = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    candidate_vote_names.remove(player.name)
    voting_message = player.get_vote(message_history, candidate_vote_names)
    for name in candidate_vote_names:
        if name in voting_message:  # update game manger
            (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(player.name)).write_text(name)
            return
    # TODO: add log that if didn't return, then voting message didn't have a possible name


def add_message_to_game(player, message_history):
    if not player.is_mafia and is_nighttime(game_dir):
        return  # only mafia can communicate during nighttime
    message = player.generate_message(message_history).strip()
    if message:
        with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(player.name), "a") as f:
            f.write(format_message(player.name, message))
        # artificially making the model taking time to write the message
        wait_writing_time(player, message)


def end_game():
    # TODO maybe add logging of something
    print(colored(GAME_ENDED_MESSAGE, OPERATOR_COLOR))


def main():
    player = get_llm_player()
    print(colored(LLM_PLAYER_LOADED_MESSAGE, MANAGER_COLOR))
    while not all_players_joined(game_dir):
        continue
    print(colored(ALL_PLAYERS_JOINED_MESSAGE, MANAGER_COLOR))
    message_history = []
    num_read_lines_manager = num_read_lines_daytime = num_read_lines_nighttime = 0
    while not is_game_over(game_dir):
        num_read_lines_manager += read_messages_from_file(
            message_history, PUBLIC_MANAGER_CHAT_FILE, num_read_lines_manager)
        # only current phase file will have new messages, so no need to run expensive is_nighttime()
        num_read_lines_daytime += read_messages_from_file(
            message_history, PUBLIC_DAYTIME_CHAT_FILE, num_read_lines_daytime)
        if player.is_mafia:  # only mafia can see what happens during nighttime
            num_read_lines_nighttime += read_messages_from_file(
                message_history, PUBLIC_NIGHTTIME_CHAT_FILE, num_read_lines_nighttime)
        if is_voted_out(player.name, game_dir):
            eliminate(player)
            break
        if is_time_to_vote(game_dir):
            get_vote_from_llm(player, message_history)
            while is_time_to_vote(game_dir):
                continue  # wait for voting time to end when all players have voted
        add_message_to_game(player, message_history)
    end_game()


if __name__ == '__main__':
    main()
