import json
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from matplotlib import pyplot as plt  # TODO add matplotlib to requirements
from game_constants import DIRS_PREFIX, PLAYER_NAMES_FILE, LLM_LOG_FILE_FORMAT, METRICS_TO_SCORE, \
    MESSAGE_PARSING_PATTERN, GAME_MANAGER_NAME, LLM_IDENTIFICATION, PERSONAL_SURVEY_FILE_FORMAT, \
    SURVEY_COMMENTS_TITLE, METRIC_NAME_AND_SCORE_DELIMITER, MAFIA_WINS_MESSAGE, WHO_WINS_FILE, \
    GAME_CONFIG_FILE, PLAYERS_KEY_IN_CONFIG, CUTTING_TO_VOTE_MESSAGE, VOTING_MESSAGE_FORMAT, \
    VOTED_OUT_MESSAGE_FORMAT, VOTING_TIME_MESSAGE_FORMAT, DAYTIME_START_PREFIX, DAYTIME, \
    NIGHTTIME_START_PREFIX, NIGHTTIME, PUBLIC_MANAGER_CHAT_FILE, PUBLIC_DAYTIME_CHAT_FILE, \
    PUBLIC_NIGHTTIME_CHAT_FILE, MAFIA_NAMES_FILE
from game_status_checks import is_voted_out
from llm_players.llm_constants import LLM_CONFIG_KEY

ANALYSIS_DIR = Path("./analysis")

MESSAGE_HISTOGRAM_Y_LIM = (0, 30)

MEAN_MARKER_STYLE = dict(marker="x", markersize=8, color="navy", markeredgewidth=3)

# manager messages types
PHASE_START = "Now it's PHASE for X minutes"
CUT_TO_VOTE = "There is only one mafia member left"
PHASE_END = "PHASE has ended, now it's time to vote"
WHO_VOTE_FOR = "X voted for Y"
WAS_VOTED_OUT = "X was voted out"
# manager messages signals
VOTING_MESSAGE_SIGNAL = VOTING_MESSAGE_FORMAT.replace("{}", "")
VOTED_OUT_SIGNAL = VOTED_OUT_MESSAGE_FORMAT.replace("{}", "")
PHASE_END_SIGNAL = VOTING_TIME_MESSAGE_FORMAT.replace("{}", "")


def avg(scores): return sum(scores) / len(scores)


class ParsedMessage:

    def __init__(self, message, llm_player_name=None):
        self.original = message
        hrs, mins, secs, name, content = re.match(MESSAGE_PARSING_PATTERN, message).groups()
        self.timestamp = 3600 * int(hrs) + 60 * int(mins) + int(secs)  # in seconds
        self.name = name
        self.is_manager = name == GAME_MANAGER_NAME
        self.is_llm = name == llm_player_name
        self.content = content
        self.words_in_message = content.split()
        self.num_words = len(self.words_in_message)
        self.manager_message_type, self.manager_message_subject = self.parse_manager_message()

    def parse_manager_message(self):
        if not self.is_manager:
            return None, None
        elif self.content.startswith(DAYTIME_START_PREFIX):
            return PHASE_START, DAYTIME
        elif self.content.startswith(NIGHTTIME_START_PREFIX):
            return PHASE_START, NIGHTTIME
        elif self.content == CUTTING_TO_VOTE_MESSAGE:
            return CUT_TO_VOTE, None
        elif self.content.endswith(PHASE_END_SIGNAL):
            return PHASE_END, self.content.removesuffix(PHASE_END_SIGNAL)
        elif VOTING_MESSAGE_SIGNAL in self.content:
            return WHO_VOTE_FOR, self.content.split(VOTING_MESSAGE_SIGNAL)  # [voter, voted for]
        elif VOTED_OUT_SIGNAL in self.content:
            return WAS_VOTED_OUT, self.content.split(VOTED_OUT_SIGNAL)[0]
        else:
            return NotImplementedError("This manager message type is new!")

    def __repr__(self):
        return self.original
    
    def copy(self):  # allows resetting timestamps in phases without overrunning them
        message_copy = ParsedMessage(self.original)
        message_copy.is_llm = self.is_llm  # otherwise will stay False as default
        return message_copy


class Phase:
    def __init__(self, messages: list[ParsedMessage] = None, active_players=None,
                 is_daytime=True, voted_out_player=None):
        self.messages = messages.copy() if messages else []
        self.active_players = active_players.copy() if active_players else []
        self.is_daytime = is_daytime
        self.voted_out_player = voted_out_player

    def __repr__(self):
        phase_type = DAYTIME if self.is_daytime else NIGHTTIME
        return f"{phase_type} Phase (w/ {len(self.active_players)} active players)"

    def copy(self):  # to use in case I don't want to overrun the timestamps in reset_timestamps
        messages = [message.copy() for message in self.messages]
        return Phase(messages, self.active_players.copy(), self.is_daytime, self.voted_out_player)

    def reset_timestamps(self, start_timestamp=None):
        if not self.messages:
            return
        if start_timestamp is None:
            min_timestamp = self.messages[0].timestamp  # a Phase instance is created after sorting
        else:
            min_timestamp = start_timestamp
        for message in self.messages:
            message.timestamp -= min_timestamp


def get_llm_player_name(all_players, game_dir):
    llm_player_name = None
    for player_name in all_players:
        if (game_dir / LLM_LOG_FILE_FORMAT.format(player_name)).exists():
            if llm_player_name is None:
                llm_player_name = player_name
            else:
                raise NotImplementedError(f"This game (ID {game_dir.name}) has more than one LLM")
    return llm_player_name


def get_survey_results(game_dir, player_name, all_metrics):
    lines = (game_dir / PERSONAL_SURVEY_FILE_FORMAT.format(player_name)).read_text().splitlines()
    results = {}
    new_line_is_comments = False
    for line in lines:
        if new_line_is_comments:
            results[SURVEY_COMMENTS_TITLE] = line
        elif line == SURVEY_COMMENTS_TITLE:
            new_line_is_comments = True
        for metric in all_metrics:
            if line.startswith(metric):
                score = re.match(fr"{metric}{METRIC_NAME_AND_SCORE_DELIMITER}(\d+)", line).group(1)
                results[metric] = int(score)
    return results


def parse_messages_by_phase(parsed_messages: list[ParsedMessage], all_players, mafia_players):
    all_phases = []
    is_daytime = True
    current_players = [player for player in all_players]
    current_mafia = [player for player in all_players if player in mafia_players]
    current_phase = Phase(active_players=current_players, is_daytime=is_daytime,
                          messages=parsed_messages[:1])
    for message in parsed_messages[1:]:  # first one is always daytime announcement
        if message.manager_message_type == PHASE_START:  # first one is skipped
            all_phases.append(current_phase)
            is_daytime = not is_daytime
            active_players = current_players if is_daytime else current_mafia
            current_phase = Phase(active_players=active_players, is_daytime=is_daytime)  # new phase
        elif message.manager_message_type == WAS_VOTED_OUT:
            voted_out_player = message.manager_message_subject
            current_players.remove(voted_out_player)
            if voted_out_player in current_mafia:
                current_mafia.remove(voted_out_player)
            current_phase.voted_out_player = voted_out_player
        current_phase.messages.append(message)
    all_phases.append(current_phase)  # the last one, since a new one wasn't started
    return all_phases


def parse_messages(game_dir, all_players, mafia_players, llm_player_name):
    manager_messages = (game_dir / PUBLIC_MANAGER_CHAT_FILE).read_text().splitlines()
    daytime_messages = (game_dir / PUBLIC_DAYTIME_CHAT_FILE).read_text().splitlines()
    nighttime_messages = (game_dir / PUBLIC_NIGHTTIME_CHAT_FILE).read_text().splitlines()
    all_messages = manager_messages + daytime_messages + nighttime_messages
    parsed_messages = [ParsedMessage(message, llm_player_name) for message in all_messages]
    parsed_messages.sort(key=lambda x: x.timestamp)
    parsed_messages_by_phase = parse_messages_by_phase(parsed_messages, all_players, mafia_players)
    return parsed_messages_by_phase


def get_single_game_results(game_id):
    game_dir = Path(DIRS_PREFIX) / game_id
    # analysis_dir = Path(ANALYSIS_DIR) / game_id  # TODO: remove?
    # analysis_dir.mkdir()  # TODO: remove?
    all_players = (game_dir / PLAYER_NAMES_FILE).read_text().splitlines()
    mafia_players = (game_dir / MAFIA_NAMES_FILE).read_text().splitlines()
    llm_player_name = get_llm_player_name(all_players, game_dir)
    assert llm_player_name, "This game has no LLM, so analysis is meaningless"
    with open(game_dir / GAME_CONFIG_FILE) as f:
        config = json.load(f)
    llm_config = [player[LLM_CONFIG_KEY] for player in config[PLAYERS_KEY_IN_CONFIG]
                  if player["name"] == llm_player_name][0]
    human_players = [player for player in all_players if player != llm_player_name]
    all_metrics = [LLM_IDENTIFICATION] + METRICS_TO_SCORE
    metrics_results = {metric: [] for metric in all_metrics}
    all_comments = []
    for player_name in human_players:
        survey_results = get_survey_results(game_dir, player_name, all_metrics)
        for metric in all_metrics:
            # in case there was a problem and not all metrics were scored
            if metric in survey_results:
                metrics_results[metric].append(survey_results[metric])
        if SURVEY_COMMENTS_TITLE in survey_results:
            all_comments.append(survey_results[SURVEY_COMMENTS_TITLE])
    parsed_messages_by_phase = parse_messages(game_dir, all_players, mafia_players, llm_player_name)
    was_llm_voted_out = is_voted_out(llm_player_name, game_dir)
    is_llm_mafia = llm_player_name in mafia_players
    did_mafia_win = MAFIA_WINS_MESSAGE in (game_dir / WHO_WINS_FILE).read_text()
    did_llm_win = did_mafia_win == is_llm_mafia
    return llm_player_name, all_players, mafia_players, human_players, llm_config, \
        metrics_results, all_comments, parsed_messages_by_phase, was_llm_voted_out, is_llm_mafia, \
        did_mafia_win, did_llm_win  # num_daytime_phases, num_nighttime_phases, and more from doc - will be in the next function to analyze


def plot_game_flow(game_id, all_players, parsed_messages_by_phase: list[Phase], llm_player_name):
    player_message_lengths = {player: [] for player in all_players}
    player_voted_out = {player: None for player in all_players}
    player_color = {player: f"C{i}" for i, player in enumerate(all_players)}
    if "C10" in player_color.values():
        # raise UserWarning("More than 10 players, which means repetition of colors in plot")
        print(UserWarning("More than 10 players, which means repetition of colors in plot"))
    title = f"Game {game_id} Flow"
    plt.title(title)
    all_timestamps = []
    phase_limits = get_game_flow_info(all_timestamps, parsed_messages_by_phase,
                                      player_message_lengths, player_voted_out)
    for player in all_players:
        if player_voted_out[player]:
            plt.scatter([player_voted_out[player]], [MESSAGE_HISTOGRAM_Y_LIM[1]],
                        color=player_color[player], alpha=0.3)
        player_label = player + " (LLM)" if player == llm_player_name else player
        plt.bar(*zip(*player_message_lengths[player]), width=7,
                label=player_label, color=player_color[player], alpha=0.3)
    for (timestamp, is_phase_end, is_daytime) in phase_limits:
        color = "dark" if is_phase_end else ""
        color += "blue" if is_daytime else "red"
        plt.axvline(timestamp, *plt.ylim(), color=color, linewidth=0.5)
    plt.xlim(min(all_timestamps) - 10, max(all_timestamps) + 10)
    plt.ylim(MESSAGE_HISTOGRAM_Y_LIM)
    plt.xlabel("timestamp")
    plt.ylabel("Number of words in message")
    plt.legend(bbox_to_anchor=(1.05, 0.5), loc="center left")
    plt.tight_layout()
    plt.savefig(ANALYSIS_DIR / (title + ".png"))
    plt.show()


def get_game_flow_info(all_timestamps, parsed_messages_by_phase, player_message_lengths,
                       player_voted_out, human_messages=True, llm_messages=True):
    phase_limits = []
    for phase in parsed_messages_by_phase:
        for message in phase.messages:
            if (message.is_llm and not llm_messages) or (not message.is_llm and not human_messages):
                continue
            all_timestamps.append(message.timestamp)
            if message.manager_message_type in (PHASE_START, PHASE_END):
                phase_limits.append((message.timestamp, message.manager_message_type == PHASE_END,
                                     message.manager_message_subject == DAYTIME))
            elif message.manager_message_type == WAS_VOTED_OUT \
                    and message.manager_message_subject in player_voted_out:
                player_voted_out[message.manager_message_subject] = message.timestamp
            elif not message.is_manager and message.name in player_message_lengths:
                player_message_lengths[message.name].append((message.timestamp, message.num_words))
    return phase_limits


def plot_messages_histogram_in_phase(all_players, phases: list[Phase], game_id=None,
                                     human_messages=True, llm_messages=True, llm_player_name=None,
                                     daytime_phases=True, nighttime_phases=False,
                                     plot_for_each_player=True, plot_general_histogram=True):
    assert daytime_phases or nighttime_phases
    if daytime_phases and nighttime_phases:
        raise UserWarning("Best to use only for daytime phases or only for nighttime phases")
    if llm_messages and plot_for_each_player and llm_player_name is None:
        raise UserWarning("You want to plot for each player separately, and to plot for the LLM, "
                          "but you haven't given the LLM name in the llm_player_name parameter")
    player_message_lengths = {player: [] for player in all_players}
    # player_voted_out = {player: None for player in all_players}
    all_timestamps = []
    color = "C0"
    for phase in phases:
        if (phase.is_daytime and not daytime_phases) \
                or (not phase.is_daytime and not nighttime_phases):
            continue
        phase_reset = phase.copy()
        phase_reset.reset_timestamps()
        get_game_flow_info(all_timestamps, [phase_reset],
                           # creates unified histogram per player across phases
                           player_message_lengths, {}, # player_voted_out,
                           human_messages=human_messages,
                           llm_messages=llm_messages)
    game_in_title = f" in game {game_id}" if game_id is not None else ""
    phase_in_title = get_phase_name(daytime_phases, nighttime_phases)
    # plot for each player separately:
    if plot_for_each_player:
        for player in all_players:
            player_label = player + " (LLM)" if player == llm_player_name else player
            title = f"Messages histogram of {player_label} for {phase_in_title}" + game_in_title
            plt.title(title)
            messages_lengths = player_message_lengths[player] if player_message_lengths[player] else [(0, 0)]
            plt.bar(*zip(*messages_lengths), width=7, color=color, alpha=0.3)
            plt.xlim(min(all_timestamps) - 10, max(all_timestamps) + 10)
            plt.ylim(MESSAGE_HISTOGRAM_Y_LIM)
            plt.xlabel("timestamp")
            plt.ylabel("Number of words in message")
            plt.savefig(ANALYSIS_DIR / (title + ".png"))
            plt.show()
    if plot_general_histogram:
        for player in all_players:
            messages_lengths = player_message_lengths[player] if player_message_lengths[player] else [(0, 0)]
            plt.bar(*zip(*messages_lengths), width=7, color=color, alpha=0.3)
        title = f"Unified Messages histogram for {phase_in_title}" + game_in_title
        plt.title(title)
        if plot_for_each_player:  # do it will be easy to compare
            plt.xlim(min(all_timestamps) - 10, max(all_timestamps) + 10)
        plt.ylim(MESSAGE_HISTOGRAM_Y_LIM)
        plt.xlabel("timestamp")
        plt.ylabel("Number of words in message")
        plt.savefig(ANALYSIS_DIR / (title + ".png"))
        plt.show()
    return player_message_lengths  #, player_voted_out


def plot_messages_histogram_in_all_games(reset_message_lengths_across_all_games, player_name=None,
                                         phase_name=None):
    color = "C0"
    plt.bar(*zip(*reset_message_lengths_across_all_games), width=7, color=color, alpha=0.3)
    player_title = "" if player_name is None else f"of {player_name} "
    phase_title = "" if phase_name is None else f"for {phase_name} "
    title = f"Unified Messages histogram {player_title}{phase_title}across all games"
    plt.title(title)
    plt.ylim(MESSAGE_HISTOGRAM_Y_LIM)
    plt.xlabel("timestamp")
    plt.ylabel("Number of words in message")
    plt.savefig(ANALYSIS_DIR / (title + ".png"))
    plt.show()


def get_phase_name(daytime_phases, nighttime_phases):
    if daytime_phases and nighttime_phases:
        return f"{DAYTIME} and {NIGHTTIME}"
    elif daytime_phases:
        return DAYTIME
    elif nighttime_phases:
        return NIGHTTIME
    else:
        raise ValueError("Must choose at least one phase")


def plot_single_pie_chart(title, result_on_all_games, true_label, false_label):
    plt.title(title)
    num_true = sum(result_on_all_games)
    num_false = len(result_on_all_games) - num_true
    plt.pie([num_true, num_false], labels=[true_label, false_label], autopct="%1.1f%%")
    plt.savefig(ANALYSIS_DIR / (title + ".png"))
    plt.show()


def plot_all_pie_charts(did_mafia_win_all_games, did_llm_win_all_games,
                        was_llm_voted_out_all_games, is_llm_mafia_all_games):
    plot_single_pie_chart("Mafia wins percentage across all games", did_mafia_win_all_games,
                          "Mafia win", "Mafia lose")
    plot_single_pie_chart("LLM win percentage across all games", did_llm_win_all_games,
                          "LLM win", "LLM lose")
    plot_single_pie_chart("Percentage of games where LLM plays as mafia", is_llm_mafia_all_games,
                          "LLM is mafia", "LLM is bystander")
    did_llm_win_as_mafia = []
    did_llm_win_as_bystander = []
    for i, is_llm_mafia in enumerate(is_llm_mafia_all_games):
        if is_llm_mafia:
            did_llm_win_as_mafia.append(did_llm_win_all_games[i])
        else:
            did_llm_win_as_bystander.append(did_llm_win_all_games[i])
    if did_llm_win_as_mafia:
        plot_single_pie_chart("LLM win percentage out of games played as mafia",
                              did_llm_win_as_mafia, "LLM win as mafia", "LLM lose as mafia")
    if did_llm_win_as_bystander:
        plot_single_pie_chart("LLM win percentage out of games played as bystander",
                              did_llm_win_as_bystander, "LLM win as bystander", "LLM lose as bystander")
    # TODO add one of was the LLM identified, and the one conditional of was it identified out of playing as mafia/bystander separately


def plot_scores_for_single_metric(metric, scores_by_game):
    title = f"{metric.capitalize()} scores across all games"
    plt.title(title + f"\n(with {MEAN_MARKER_STYLE['marker']}-markers "
                      f"for means and error bars for +-STD)")
    plt.xlabel("games")
    plt.ylabel(metric)
    # TODO: set ylim by low and high limits in constants!
    x = []
    y = []
    means = []
    stds = []
    for i, game in enumerate(scores_by_game):
        x += [i] * len(game)
        y += [score for score in game]
        means.append(game.mean())
        stds.append(game.std())
    plt.scatter(x, y)
    plt.errorbar(range(len(scores_by_game)), means, stds, linestyle="none", **MEAN_MARKER_STYLE)
    plt.xticks([], [])
    plt.savefig(ANALYSIS_DIR / (title + ".png"))
    plt.show()
    return np.mean(y), np.std(y)


def plot_metric_scores(metrics_results_all_games):
    metrics = list(metrics_results_all_games.keys())  # to ensure order
    # if LLM_IDENTIFICATION in metrics:  # TODO: cancel this removal after the question is back in games!
    #     metrics.remove(LLM_IDENTIFICATION)
    means_by_metrics = []
    stds_by_metrics = []
    for metric in metrics:
        mean, std = plot_scores_for_single_metric(metric, metrics_results_all_games[metric])
        means_by_metrics.append(mean)
        stds_by_metrics.append(std)
    title = "Distributions of all metrics across all games"
    plt.title(title + f"\n(with {MEAN_MARKER_STYLE['marker']}-markers "
                      f"for means and error bars for +-STD)")
    # TODO: set ylim by low and high limits in constants!
    plt.errorbar(metrics, means_by_metrics, stds_by_metrics, linestyle="none", **MEAN_MARKER_STYLE)
    plt.savefig(ANALYSIS_DIR / (title + ".png"))
    plt.show()


def main():
    # game_ids = ["0036", "0037", "0027", "0028", "0030", "0032"]
    # game_ids = ["0051"]
    # game_ids = ["0051", "0056", "0057", "0058", "0059", "0060"]
    # game_ids = ["0064", "0065", "0067", "0068", "0069", "0070", "0071", "0072", "0073"]
    game_ids = ["0051", "0056", "0057", "0058", "0059", "0060", "0064", "0065", "0067", "0068", "0069", "0070", "0071", "0072", "0073"]

    hist_for_daytime_phases = True
    hist_for_nighttime_phases = False

    did_mafia_win_all_games = []
    did_llm_win_all_games = []
    was_llm_voted_out_all_games = []
    is_llm_mafia_all_games = []
    metrics_results_all_games = defaultdict(list)

    reset_message_lengths_across_all_games = []
    for game_id in game_ids:

        llm_player_name, all_players, mafia_players, human_players, llm_config, \
            metrics_results, all_comments, parsed_messages_by_phase, was_llm_voted_out, \
            is_llm_mafia, did_mafia_win, did_llm_win = get_single_game_results(game_id)

        (ANALYSIS_DIR / ("game" + game_id + "_comments.txt")).write_text("\n".join(all_comments))

        if LLM_IDENTIFICATION in metrics_results:
            plot_single_pie_chart(f"Percentage of LLM identification in game {game_id}",
                                  metrics_results[LLM_IDENTIFICATION],
                                  "LLM was identified", "LLM was not identified")

        did_mafia_win_all_games.append(did_mafia_win)
        did_llm_win_all_games.append(did_llm_win)
        was_llm_voted_out_all_games.append(was_llm_voted_out)
        is_llm_mafia_all_games.append(is_llm_mafia)
        for metric in metrics_results:
            metrics_results_all_games[metric].append(np.array(metrics_results[metric]))

        plot_game_flow(game_id, all_players, parsed_messages_by_phase, llm_player_name)
        # # plot_game_flow(game_id, human_players, parsed_messages_by_phase, llm_player_name)
        # plot_game_flow(game_id, [llm_player_name], parsed_messages_by_phase, llm_player_name)
        player_message_lengths = plot_messages_histogram_in_phase(
            all_players, parsed_messages_by_phase, game_id=game_id, llm_player_name=llm_player_name,
            daytime_phases=hist_for_daytime_phases, nighttime_phases=hist_for_nighttime_phases,
        )
        for player in player_message_lengths:
            reset_message_lengths_across_all_games += player_message_lengths[player]

    phase_name = get_phase_name(hist_for_daytime_phases, hist_for_nighttime_phases)
    plot_messages_histogram_in_all_games(reset_message_lengths_across_all_games,
                                         phase_name=phase_name)

    plot_all_pie_charts(did_mafia_win_all_games, did_llm_win_all_games,
                        was_llm_voted_out_all_games, is_llm_mafia_all_games)

    plot_metric_scores(metrics_results_all_games)

    llm_only_reset_message_lengths_across_all_games = []
    human_only_reset_message_lengths_across_all_games = []
    for game_id in game_ids:  # Yes, I'm aware this is currently repetition of calculation...
        llm_player_name, all_players, mafia_players, human_players, llm_config, \
            metrics_results, all_comments, parsed_messages_by_phase, was_llm_voted_out, \
            is_llm_mafia, did_mafia_win, did_llm_win = get_single_game_results(game_id)
        player_message_lengths = plot_messages_histogram_in_phase(
            [llm_player_name], parsed_messages_by_phase, game_id=game_id,
            llm_player_name=llm_player_name, plot_general_histogram=False, plot_for_each_player=False,
            daytime_phases=hist_for_daytime_phases, nighttime_phases=hist_for_nighttime_phases,
        )
        llm_only_reset_message_lengths_across_all_games += player_message_lengths[llm_player_name]
        player_message_lengths = plot_messages_histogram_in_phase(
            human_players, parsed_messages_by_phase, game_id=game_id,
            plot_general_histogram=False, plot_for_each_player=False,
            daytime_phases=hist_for_daytime_phases, nighttime_phases=hist_for_nighttime_phases,
        )
        for player in player_message_lengths:
            human_only_reset_message_lengths_across_all_games += player_message_lengths[player]
    phase_name = get_phase_name(hist_for_daytime_phases, hist_for_nighttime_phases)
    plot_messages_histogram_in_all_games(llm_only_reset_message_lengths_across_all_games,
                                         phase_name=phase_name, player_name="LLM")
    plot_messages_histogram_in_all_games(human_only_reset_message_lengths_across_all_games,
                                         phase_name=phase_name, player_name="human-players")


def get_games_statistics():
    all_games = []
    number_of_phases_per_game = {}
    all_messages_per_game = {}
    llm_messages_per_game = {}
    all_players_per_game = {}
    did_llm_win_per_game = {}
    all_metrics = [LLM_IDENTIFICATION] + METRICS_TO_SCORE
    metrics_per_game = {metric: {} for metric in all_metrics}
    for game_dir in Path(DIRS_PREFIX).glob("*"):
        if game_dir.is_dir() and game_dir.name.isdigit() and "00001" not in game_dir.name:
            all_games.append(game_dir)
            __llm_player_name, all_players, __mafia_players, __human_players, __llm_config, \
                metrics_results, __all_comments, parsed_messages_by_phase, __was_llm_voted_out, \
                __is_llm_mafia, __did_mafia_win, did_llm_win = get_single_game_results(game_dir.name)
            number_of_phases_per_game[game_dir.name] = len(parsed_messages_by_phase)
            all_messages_including_manager = sum([phase.messages for phase in parsed_messages_by_phase], [])
            all_messages_per_game[game_dir.name] = [msg for msg in all_messages_including_manager if not msg.is_manager]
            llm_messages_per_game[game_dir.name] = [msg for msg in all_messages_per_game[game_dir.name] if msg.is_llm]
            all_players_per_game[game_dir.name] = all_players
            did_llm_win_per_game[game_dir.name] = did_llm_win
            for metric in metrics_results:
                if int(game_dir.name) < 40:  # no identification and others are 0 to 100
                    if metric in METRICS_TO_SCORE:
                        metrics_per_game[metric][game_dir.name] = avg([score / 100 for score in metrics_results[metric]])
                else:
                    metrics_per_game[metric][game_dir.name] = avg(metrics_results[metric])
    num_players = [len(v) for v in all_players_per_game.values()]
    print(f"# Games: {len(all_games)}\n"
          f"Avg # Phases: {avg(number_of_phases_per_game.values())}\n"
          f"Avg # Players: {avg(num_players)}\n"
          f"\tSTD of # Players: {np.std(num_players)}\n"
          f"\tMin of # Players: {min(num_players)}\n"
          f"\tMax of # Players: {max(num_players)}\n"
          f"Avg # Messages: {avg([len(v) for v in all_messages_per_game.values()])}\n"
          f"LLM Avg # Messages: {avg([len(v) for v in llm_messages_per_game.values()])}\n"
          f"Win %: {avg(did_llm_win_per_game.values())}\n"
          f"\n")
    for metric in metrics_per_game:
        print(f"{metric}: {avg(metrics_per_game[metric].values())}")
    print()
    multiple_games_stats = [3] * (7 * 2) + [2] + [1] * 8 + [1] * (6 * 3) + [1] * 4 + [2] * 2 + [1] * 4 + [3] * 2 + [
        5] * (2 + 2) + [4] * 3 + [6] * 4
    """the 3s in the beginning are the people in the pilot except Asaf, then the 2 is Asaf, then the 8 new people in A400, 
    then we had 5 games in the aquarium with 6 new each time, except of game 0059 and 0060 that had 2 players who played both,
    then pizza night: Itai's 2 friends were for 3 games, then Itai and Roy played 5, Barr, Dan and almog played 4, Aviad and Guy played 5, Shaked, Yoav, Meitar, Shir played 6  
    """  # TODO leave out!
    print(f"statistics of players playing in multiple games:\n"
          f"Average: {avg(multiple_games_stats)}\n"
          f"STD: {np.std(multiple_games_stats)}\n"
          f"Min: {min(multiple_games_stats)}\n"
          f"Max: {max(multiple_games_stats)}\n")



if __name__ == '__main__':
    # main()
    get_games_statistics()
