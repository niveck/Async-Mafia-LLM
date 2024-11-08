import json
import os
import sys
import time  # already in constants...
from pathlib import Path
from persons.asynchronous_persons.mafia_players.llm_mafia import LLMMafia
from game_constants import *


# global variable for the game dir
game_dir = Path()  # will be updated only if __name__ == __main__ (prevents new ones in imports)


class Player:

    def __init__(self, name, is_mafia, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.personal_chat_file = self._create_personal_file(PERSONAL_CHAT_FILE_FORMAT)
        self.personal_chat_file_lines_read = 0
        self.personal_vote_file = self._create_personal_file(PERSONAL_VOTE_FILE_FORMAT)
        self.personal_vote_file_last_modified = os.path.getmtime(self.personal_vote_file)
        # status is whether the player was vote out
        self.personal_status_file = self._create_personal_file(PERSONAL_STATUS_FILE_FORMAT)

    def _create_personal_file(self, file_name_format):
        new_file = game_dir / file_name_format.format(self.name)
        new_file.touch()
        return new_file

    def get_new_messages(self):
        with open(self.personal_chat_file, "r") as f:
            # the readlines method includes the "\n"
            lines = f.readlines()[self.personal_chat_file_lines_read:]
        self.personal_chat_file_lines_read += len(lines)
        return lines

    def get_voted_player(self):
        return self.personal_vote_file.read_text().strip()

    def did_cast_new_vote(self):
        last_modified = os.path.getmtime(self.personal_vote_file)
        if last_modified > self.personal_vote_file_last_modified:
            self.personal_vote_file_last_modified = last_modified
            return True
        else:
            return False

    def eliminate(self):
        self.personal_status_file.write_text(VOTED_OUT)


def init_game():
    global game_dir  # TODO maybe add mechanism for using a game key (something like MGSZX) instead
    game_dir = Path(DIRS_PREFIX) / time.strftime("%d%m%y_%H%M")
    game_dir.mkdir(mode=0o777)
    with open(sys.argv[1]) as f:
        config = json.load(f)
    players = [Player(**player_config) for player_config in config["players"]]
    all_names_str = "\n".join([player.name for player in players])
    (game_dir / PLAYER_NAMES_FILE).write_text(all_names_str)
    (game_dir / REMAINING_PLAYERS_FILE).write_text(all_names_str)
    all_mafia_names_str = [player.name for player in players if player.is_mafia]
    (game_dir / MAFIA_NAMES_FILE).write_text("\n".join(all_mafia_names_str))
    (game_dir / PHASE_STATUS_FILE).write_text(NIGHTTIME)
    (game_dir / PUBLIC_MANAGER_CHAT_FILE).touch()
    (game_dir / PUBLIC_DAYTIME_CHAT_FILE).touch()
    (game_dir / PUBLIC_NIGHTTIME_CHAT_FILE).touch()
    (game_dir / WHO_WINS_FILE).touch()
    return players


def is_win_by_bystanders(mafia_players):
    if len(mafia_players) == 0:
        (game_dir / WHO_WINS_FILE).write_text(BYSTANDERS_WIN_MESSAGE)
        return True
    return False


def is_win_by_mafia(mafia_players, bystanders):
    if len(mafia_players) >= len(bystanders):
        (game_dir / WHO_WINS_FILE).write_text(MAFIA_WINS_MESSAGE)
        return True
    return False


def is_game_over(players):
    mafia_players = [player for player in players if player.is_mafia]
    bystanders = [player for player in players if not player.is_mafia]
    return is_win_by_bystanders(mafia_players) or is_win_by_mafia(mafia_players, bystanders)


def run_chat_round_between_players(players, chat_room):
    for player in players:
        lines = player.get_new_messages()
        with open(chat_room, "a") as f:
            f.writelines(lines)  # lines already include "\n"
        if player.did_cast_new_vote():
            with open(chat_room, "a") as f:
                voting_message = VOTING_MESSAGE_FORMAT.format(player.name, player.get_voted_player())
                f.write(format_message(GAME_MANAGER_NAME, voting_message))


def get_voted_out_player(voting_players, optional_votes_players):
    votes = {player.name: 0 for player in optional_votes_players}
    for player in voting_players:
        voted_for = player.get_voted_player()
        if voted_for in votes:
            votes[voted_for] += 1
    # if there were invalid votes or if there was a tie, decision will be made "randomly"
    voted_out_name = max(votes, key=votes.get)
    # update info file of remaining players
    remaining_players = (game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
    remaining_players.remove(voted_out_name)
    (game_dir / REMAINING_PLAYERS_FILE).write_text("\n".join(remaining_players))
    # update player object status
    voted_out_player = {player.name: player for player in optional_votes_players}[voted_out_name]
    voted_out_player.eliminate()
    return voted_out_player


def game_manager_announcement(message):
    with open(game_dir / PUBLIC_MANAGER_CHAT_FILE, "a") as f:
        f.write(format_message(GAME_MANAGER_NAME, message))


def announce_voted_out_player(voted_out_player):
    role = get_role_string(voted_out_player.is_mafia)
    voted_out_message = VOTED_OUT_MESSAGE_FORMAT.format(voted_out_player.name, role)
    game_manager_announcement(voted_out_message)


def run_phase(players, voting_players, optional_votes_players, public_chat_file, time_limit_seconds):
    start_time = time.time()
    while time.time() - start_time < time_limit_seconds:
        run_chat_round_between_players(voting_players, public_chat_file)
    voted_out_player = get_voted_out_player(voting_players, optional_votes_players)
    players.remove(voted_out_player)
    announce_voted_out_player(voted_out_player)


def announce_nighttime():
    game_manager_announcement(NIGHTTIME_BEGINNING_MESSAGE)


def run_nighttime(players):
    (game_dir / PHASE_STATUS_FILE).write_text(NIGHTTIME)
    mafia_players = [player for player in players if player.is_mafia]
    bystanders = [player for player in players if not player.is_mafia]
    announce_nighttime()
    run_phase(players, mafia_players, bystanders, game_dir / PUBLIC_NIGHTTIME_CHAT_FILE,
              NIGHTTIME_TIME_LIMIT_SECONDS)


def announce_daytime():
    game_manager_announcement(DAYTIME_BEGINNING_MESSAGE)


def run_daytime(players):
    (game_dir / PHASE_STATUS_FILE).write_text(DAYTIME)
    announce_daytime()
    run_phase(players, players, players, game_dir / PUBLIC_DAYTIME_CHAT_FILE,
              DAYTIME_TIME_LIMIT_SECONDS)


def wait_for_players(players):
    # TODO: this is only temporary,
    #  maybe use something automatic, like all players need to sign up in their files...
    input("As game manager, use Enter to start the game after all players have entered: ")
    print("Game is now running! It's content is displayed to players.")


def end_game():
    print("Game has finished.")  # TODO: maybe log the game somehow? maybe save important details?..


def main():
    if len(sys.argv) != 2:
        raise ValueError(f"Usage: {Path(__file__).name} <json configuration path>")
    players = init_game()
    wait_for_players(players)
    while not is_game_over(players):
        run_nighttime(players)
        run_daytime(players)
    end_game()


if __name__ == '__main__':
    main()
