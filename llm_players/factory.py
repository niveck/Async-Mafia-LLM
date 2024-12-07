from llm_players.llm_constants import LLM_CONFIG_KEY, ASYNC_TYPE_KEY
from llm_players.fine_tuned_player import FineTunedPlayer
from llm_players.generate_then_schedule_player import GenerateThenSchedulePlayer
from llm_players.schedule_then_generate_player import ScheduleThenGeneratePlayer


llm_players_classes = {
    FineTunedPlayer.TYPE_NAME: FineTunedPlayer,
    ScheduleThenGeneratePlayer.TYPE_NAME: ScheduleThenGeneratePlayer,
    GenerateThenSchedulePlayer.TYPE_NAME: GenerateThenSchedulePlayer,
}


def llm_player_factory(player_config):
    player_class = llm_players_classes[player_config[LLM_CONFIG_KEY][ASYNC_TYPE_KEY]]
    return player_class(**player_config)
