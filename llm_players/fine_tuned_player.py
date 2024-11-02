from llm_players.llm_player import LLMPlayer

DEFAULT_MODEL_PATH = ""  # TODO add the model path for my fine tuned mafia model


class FineTunedPlayer(LLMPlayer):

    TYPE_NAME = "fine_tuned"

    def __init__(self, name, is_mafia, **kwargs):
        model_name = kwargs.get("model_name", DEFAULT_MODEL_PATH)
        kwargs["model_name"] = model_name  # setting the default model path for fine-tuned player
        super().__init__(name, is_mafia, **kwargs)

    def create_prompt(self, message_history):
        pass  # TODO implement! involves pre processing of the messages!

    def should_generate_message(self, potential_answer):
        return bool(potential_answer) and self.pass_turn_token not in potential_answer

    def generate_message(self, message_history):
        prompt = self.create_prompt(message_history)
        potential_answer = self.llm.generate(prompt)
        if self.should_generate_message(potential_answer):
            return potential_answer
        else:
            return None
