from abc import ABC, abstractmethod
from game_constants import get_role_string, GAME_START_TIME_FILE
from llm_players.llm_constants import turn_task_into_prompt, GENERAL_SYSTEM_INFO, \
    PASS_TURN_TOKEN_KEY, USE_TURN_TOKEN_KEY, WORDS_PER_SECOND_WAITING_KEY
from llm_players.llm_wrapper import LLMWrapper
from llm_players.logger import Logger


class LLMPlayer(ABC):

    TYPE_NAME = None

    def __init__(self, name, is_mafia, llm_config, game_dir, **kwargs):
        self.name = name
        self.is_mafia = is_mafia
        self.role = get_role_string(is_mafia)
        self.game_dir = game_dir
        self.logger = Logger(name, game_dir)
        self.pass_turn_token = llm_config[PASS_TURN_TOKEN_KEY]
        self.use_turn_token = llm_config[USE_TURN_TOKEN_KEY]
        self.num_words_per_second_to_wait = llm_config[WORDS_PER_SECOND_WAITING_KEY]
        self.llm = LLMWrapper(self.logger, **llm_config)

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
        system_info = self.get_system_info_message()
        self.logger.log("prompt for get_vote", prompt)
        self.logger.log("system_info for get_vote", system_info)
        vote = self.llm.generate(prompt, system_info)
        self.logger.log("generated vote in get_vote", vote)
        return vote
