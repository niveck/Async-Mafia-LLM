from abc import ABC, abstractmethod
from game_constants import get_role_string, DEFAULT_PASS_TURN_TOKEN, DEFAULT_USE_TURN_TOKEN
from llm_players.llm_wrapper import LLMWrapper


class LLMPlayer(ABC):

    TYPE_NAME = None

    def __init__(self, name, is_mafia, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.role = get_role_string(is_mafia)
        self.pass_turn_token = kwargs.get("pass_turn_token", DEFAULT_PASS_TURN_TOKEN)
        self.use_turn_token = kwargs.get("use_turn_token", DEFAULT_USE_TURN_TOKEN)
        self.llm = LLMWrapper(**kwargs)

    @abstractmethod
    def should_generate_message(self, context):
        raise NotImplementedError()

    @abstractmethod
    def generate_message(self, message_history):
        raise NotImplementedError()
