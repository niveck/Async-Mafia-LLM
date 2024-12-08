from llm_players.llm_constants import FINE_TUNED_TYPE
from llm_players.llm_player import LLMPlayer

DEFAULT_MODEL_PATH = ""  # TODO add the model path for my fine tuned mafia model


class FineTunedPlayer(LLMPlayer):  # TODO: use self.logger

    TYPE_NAME = FINE_TUNED_TYPE

    def __init__(self, **kwargs):
        model_name = kwargs.get("model_name", DEFAULT_MODEL_PATH)
        kwargs["model_name"] = model_name  # setting the default model path for fine-tuned player  # TODO: needs to be refactored, now it's not working anymore
        super().__init__(**kwargs)

    def create_prompt(self, message_history):
        raise NotImplementedError()  # TODO implement! involves pre processing of the messages!

    def should_generate_message(self, potential_answer):
        return bool(potential_answer) and self.pass_turn_token not in potential_answer

    def generate_message(self, message_history):
        prompt = self.create_prompt(message_history)
        potential_answer = self.llm.generate(prompt)
        if self.should_generate_message(potential_answer):
            return potential_answer
        else:
            return ""

    def get_vote(self, message_history, candidate_vote_names):
        raise NotImplementedError()  # TODO implement! needs to overrun the prompting default
