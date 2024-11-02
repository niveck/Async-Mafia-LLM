from llm_players.fine_tuned_player import FineTunedPlayer
from llm_players.generate_then_schedule_player import GenerateThenSchedulePlayer
from llm_players.schedule_then_generate_player import ScheduleThenGeneratePlayer

DEFAULT_ASYNC_TYPE = ""  # TODO put here the TYPE_NAME attribute of the wanted class

llm_players_classes = {
    FineTunedPlayer.TYPE_NAME: FineTunedPlayer,
    ScheduleThenGeneratePlayer.TYPE_NAME: ScheduleThenGeneratePlayer,
    GenerateThenSchedulePlayer.TYPE_NAME: GenerateThenSchedulePlayer,
    # TODO dict of TYPE_NAME to class
}


def llm_player_factory(player_config):
    async_type = player_config.get("async_type", DEFAULT_ASYNC_TYPE)
    player_class = llm_players_classes.get(async_type, llm_players_classes[DEFAULT_ASYNC_TYPE])
    return player_class(**player_config)
