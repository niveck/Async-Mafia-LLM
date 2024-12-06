from game_constants import NIGHTTIME, PHASE_STATUS_FILE, WHO_WINS_FILE, VOTED_OUT, \
    PERSONAL_STATUS_FILE_FORMAT, VOTING_TIME, GAME_START_TIME_FILE


def is_nighttime(game_dir):
    return NIGHTTIME in (game_dir / PHASE_STATUS_FILE).read_text()


def is_game_over(game_dir):
    return bool((game_dir / WHO_WINS_FILE).read_text())  # if someone wins, the file isn't empty


def is_voted_out(name, game_dir):
    return VOTED_OUT in (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).read_text()


def is_time_to_vote(game_dir):
    return VOTING_TIME in (game_dir / PHASE_STATUS_FILE).read_text()


def all_players_joined(game_dir):
    # game is started by manager after all players joined, and then the file will not be empty
    return bool((game_dir / GAME_START_TIME_FILE).read_text())
