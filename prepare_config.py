import json
import argparse
import random
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from game_constants import DEFAULT_CONFIG_DIR, DEFAULT_NUM_PLAYERS, DEFAULT_NUM_MAFIA, \
    MINIMUM_NUM_PLAYERS_FOR_ONE_MAFIA, MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA, OPTIONAL_CODE_NAMES, \
    WARNING_LIMIT_NUM_MAFIA, PLAYERS_KEY_IN_CONFIG


@dataclass
class PlayerConfig:  # TODO maybe add an LLM sub-config dict
    name: str  # code name from the game's pool (in constants file)
    real_name: str = ""
    is_mafia: bool = False
    is_llm: bool = False


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default=None, help="output config file name")
    parser.add_argument("-p", "--players", default=None, help="total number of players in game")
    parser.add_argument("-m", "--mafia", default=None, help="number of mafia players in game")
    parser.add_argument("-l", "--llm", type=int, default=1, choices=[0, 1],
                        # since participants will rank the (single) LLM player performance
                        help="number of LLM players in game, currently supports maximum 1")
    parser.add_argument("-b", "--bystander", action="store_true",
                        help="whether the LLM player can only be bystander (not mafia)")
    parser.add_argument("-n", "--names_file", default=None,
                        help="path to file with the participating players' real names "
                             "(before code names assignment), separated by new line breaks ('\\n')")
    args = parser.parse_args()
    return args


def handle_output_file(args):
    output_file = args.output
    if output_file is None:
        output_file = DEFAULT_CONFIG_DIR + "/config" + time.strftime("%d%m%y_%H%M") + ".json"
    output_file = Path(output_file)
    if output_file.exists():
        input("Warning: the destination output path already exists... "
              "[enter to continue, Ctrl+C to cancel]")
    else:
        output_file.touch()  # to raise an error immediately if the new path is invalid
    return output_file


def handle_num_players(args):
    num_players = args.players
    if num_players is None:
        print(f"Using default number of total players: {DEFAULT_NUM_PLAYERS}")
        num_players = DEFAULT_NUM_PLAYERS
    elif num_players < MINIMUM_NUM_PLAYERS_FOR_ONE_MAFIA:
        raise ValueError(f"{num_players} is not enough players to play a game!"
                         f"Minimum is {MINIMUM_NUM_PLAYERS_FOR_ONE_MAFIA} players.")
    num_mafia = args.mafia
    if num_mafia is None:
        num_mafia = DEFAULT_NUM_MAFIA
    if num_mafia > 1 and num_players < MINIMUM_NUM_PLAYERS_FOR_MULT_MAFIA:
        raise ValueError(f"With only {num_players} players you can only have one mafia!")
    elif num_mafia >= WARNING_LIMIT_NUM_MAFIA:
        print(f"Pay attention that {num_mafia} mafia players might be too many "
              f"if you don't have enough players in total...")
    code_names = random.sample(OPTIONAL_CODE_NAMES, num_players)
    player_configs = [PlayerConfig(code_name) for code_name in code_names]
    mafia_players = random.sample(player_configs, num_mafia)
    for mafia_player in mafia_players:
        mafia_player.is_mafia = True
    return player_configs


def handle_llm_participation(args, player_configs):
    num_llms = args.llm
    print(f"Using {num_llms} LLM player{'' if num_llms == 1 else ''}")
    if num_llms > 0:
        if args.bystander:
            print("The LLM can only be a bystander, not mafia")
            potential_llm_players = [player_config for player_config in player_configs
                                     if not player_config.is_mafia]
        else:
            print("The LLM will be assigned a bystander/mafia role randomly "
                  "(use -b/--bystander to only use the LLM as a bystander)")
            potential_llm_players = player_configs
        llm_players = random.sample(potential_llm_players, num_llms)
        for i, llm_player in enumerate(llm_players):
            llm_player.is_llm = True
            llm_player.real_name = f"LLM{i}"


def assign_real_names(args, player_configs):
    human_players = [player_config for player_config in player_configs if not player_config.is_llm]
    if args.names_file is None:
        real_names = []
    else:  # split() removes the '\n' and ignores empty lines
        real_names = Path(args.names_file).read_text().split()
    print("The given real names of participating players:")
    print(",  ".join([f"{i + 1}. {name}" for i, name in enumerate(real_names)]))
    if len(human_players) < len(real_names):
        print(f"Warning: {len(real_names)} participating names given, "
              f"only {len(human_players)} needed for human players, "
              f"using only the first {len(human_players)}...")
        real_names = real_names[:len(human_players)]
    elif len(human_players) < len(real_names):
        while len(human_players) < len(real_names):
            real_names.append(input("Still not enough participating names, "
                                    "provide another one: ").strip())
    # now len(human_players) == len(real_names)
    for human_player, real_name in zip(human_players, real_names):
        human_player.real_name = real_name


def save_config(output_file, player_configs):
    config = {PLAYERS_KEY_IN_CONFIG: [asdict(player_config) for player_config in player_configs],
              "notes": input("Add notes to this config: [or enter to skip] ").strip()}
    with open(output_file, "w") as f:
        json.dump(config, f, indent=4)
    print(f"Configuration was created and saved to: {output_file}")


def main():
    args = parse_args()
    output_file = handle_output_file(args)  # done first to immediately raise error if invalid
    player_configs = handle_num_players(args)
    handle_llm_participation(args, player_configs)
    assign_real_names(args, player_configs)
    save_config(output_file, player_configs)


if __name__ == '__main__':
    main()