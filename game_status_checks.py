from game_constants import NIGHTTIME, PHASE_STATUS_FILE, WHO_WINS_FILE, VOTED_OUT, \
    PERSONAL_STATUS_FILE_FORMAT, DAYTIME_END_MESSAGE, NIGHTTIME_END_MESSAGE


def is_nighttime(game_dir):
    return NIGHTTIME in (game_dir / PHASE_STATUS_FILE).read_text()


def is_game_over(game_dir):
    return bool((game_dir / WHO_WINS_FILE).read_text())  # if someone wins, the file isn't empty


def is_voted_out(name, game_dir):
    return VOTED_OUT in (game_dir / PERSONAL_STATUS_FILE_FORMAT.format(name)).read_text()


def check_for_time_to_vote(line):
    return DAYTIME_END_MESSAGE in line or NIGHTTIME_END_MESSAGE in line
