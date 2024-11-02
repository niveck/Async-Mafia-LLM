from llm_players.llm_player import LLMPlayer
from llm_players.llm_wrapper import LLMWrapper


class ScheduleThenGeneratePlayer(LLMPlayer):

    TYPE_NAME = "schedule_then_generate"

    def __init__(self, name, is_mafia, **kwargs):
        super().__init__(name, is_mafia, **kwargs)
        scheduler_kwargs = kwargs.get("scheduler_kwargs", kwargs)
        self.scheduler = LLMWrapper(**scheduler_kwargs)

    def should_generate_message(self, message_history):
        context = self.create_context_for_scheduler(message_history)
        decision = self.scheduler.generate(context)
        return bool(decision) and self.pass_turn_token not in decision

    def generate_message(self, message_history):
        if self.should_generate_message(message_history):
            prompt = self.create_generation_prompt(message_history)
            return self.llm.generate(prompt)
        else:
            return None

    def create_context_for_scheduler(self, potential_answer):
        pass  # TODO!!!

    def create_generation_prompt(self, message_history):
        pass  # TODO!!!
