from abc import ABC, abstractmethod
from game_constants import get_role_string, DEFAULT_PASS_TURN_TOKEN, DEFAULT_USE_TURN_TOKEN, \
    GENERAL_SYSTEM_INFO, GAME_START_TIME_FILE
from llm_players.llm_constants import turn_task_into_prompt
from llm_players.llm_wrapper import LLMWrapper


class LLMPlayer(ABC):

    TYPE_NAME = None

    def __init__(self, name, is_mafia, game_dir, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.role = get_role_string(is_mafia)
        self.game_dir = game_dir
        self.pass_turn_token = kwargs.get("pass_turn_token", DEFAULT_PASS_TURN_TOKEN)
        self.use_turn_token = kwargs.get("use_turn_token", DEFAULT_USE_TURN_TOKEN)
        self.llm = LLMWrapper(**kwargs)

    def get_system_info_message(self):
        system_info = f"Your name is {self.name}. {GENERAL_SYSTEM_INFO}\n" \
                      f"You were assigned the following role: {self.role}.\n"
        chat_room_open_time = (self.game_dir / GAME_START_TIME_FILE).read_text().strip()
        if chat_room_open_time:  # if the game has started, the file isn't empty
            system_info += f"The game's chat room was open at [{chat_room_open_time}].\n"
        return system_info

    @abstractmethod
    def should_generate_message(self, context):
        raise NotImplementedError()

    @abstractmethod
    def generate_message(self, message_history):
        raise NotImplementedError()

    def get_vote(self, message_history, candidate_vote_names):
        task = "From the following remaining players, which player you want to vote for to " \
               "eliminate? Reply with only one name from the list, and nothing but the name: "
        task += ", ".join(candidate_vote_names)
        prompt = turn_task_into_prompt(task, message_history)
        return self.llm.generate(prompt, self.get_system_info_message())
