import json
import os
import re
import sys
from pathlib import Path
from termcolor import colored
from game_constants import *
from game_status_checks import is_nighttime, is_game_over, is_voted_out
from llm_players.factory import llm_player_factory

OPERATOR_COLOR = "yellow"  # the person running this file is the "operator" of the model
GAME_ENDED_MESSAGE = "Game has ended, without being voted out!"
WORDS_PER_SECOND_TO_WAIT = 3  # simulates the amount of words written normally per second  # TODO change such that using this feature will be determined by the LLM config in the game config


# global variable
input(colored("Press enter only after the main game code started running...",  # to get latest dir
              OPERATOR_COLOR))  # TODO maybe change it to get an argument for the game's key
game_dir = max(Path(DIRS_PREFIX).glob("*"), key=os.path.getmtime)  # latest modified dir


def get_llm_player():
    if len(sys.argv) != 3:
        raise ValueError(f"Usage: {Path(__file__).name} <json configuration path> <player name>")
    config_path, player_name = sys.argv[1], sys.argv[2]
    with open(config_path) as f:
        config = json.load(f)
    player_config = None
    for player in config[PLAYERS_KEY_IN_CONFIG]:
        if player["name"].lower() == player_name.lower():
            player_config = player
            break
    if player_config is None:
        raise ValueError(f"Wrong input: '{player_name}' is not a name in the game "
                         f"configured in {config_path}")
    player_config["game_dir"] = game_dir
    return llm_player_factory(player_config)


def read_messages_from_file(message_history, file_name, num_read_lines):
    with open(game_dir / file_name, "r") as f:
        lines = f.readlines()[num_read_lines:]
    message_history.extend(lines)  # TODO validate it updates the outer scope list
    return len(lines)


def wait_writing_time(message):
    num_words = len(message.split())
    time.sleep(num_words // WORDS_PER_SECOND_TO_WAIT)


def eliminate(player):
    # TODO print in OPERATOR_COLOR that it was eliminated, maybe log how much time it lasted in the game, how many players were left when it was voted out and maybe how many time it was voted for
    pass


def match_llm_voting_format(message):
    return re.match(LLM_VOTING_PATTERN, message)


def update_vote(message, name):
    voted_name = re.findall(LLM_VOTING_PATTERN, message)[0]
    (game_dir / PERSONAL_VOTE_FILE_FORMAT.format(name)).write_text(voted_name)


def add_message_to_game(player, message_history):
    if not player.is_mafia and is_nighttime(game_dir):
        return  # only mafia can communicate during nighttime
    message = player.generate_message(message_history).strip()
    if message:
        if match_llm_voting_format(message):
            # TODO maybe log the way it outputted only the voting format
            update_vote(message, player.name)
        else:
            # TODO maybe log that the message was not matched as a vote?...
            with open(game_dir / PERSONAL_CHAT_FILE_FORMAT.format(player.name), "a") as f:
                f.write(format_message(player.name, message))
        wait_writing_time(message)  # artificially making the model taking time to write the message


def end_game():
    # TODO maybe add logging of something
    print(colored(GAME_ENDED_MESSAGE, OPERATOR_COLOR))


def main():
    player = get_llm_player()
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
        add_message_to_game(player, message_history)
    end_game()


if __name__ == '__main__':
    main()
