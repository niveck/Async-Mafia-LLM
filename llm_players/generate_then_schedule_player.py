from llm_players.llm_player import LLMPlayer
from llm_players.llm_wrapper import LLMWrapper


class GenerateThenSchedulePlayer(LLMPlayer):

    TYPE_NAME = "schedule_then_generate"

    def __init__(self, name, is_mafia, **kwargs):
        super().__init__(name, is_mafia, **kwargs)
        scheduler_kwargs = kwargs.get("scheduler_kwargs", kwargs)
        self.scheduler = LLMWrapper(**scheduler_kwargs)

    def should_generate_message(self, potential_answer):
        context = self.create_context_for_scheduler(potential_answer)
        decision = self.scheduler.generate(context)
        return bool(decision) and self.pass_turn_token not in decision

    def generate_message(self, message_history):
        prompt = self.create_generation_prompt(message_history)
        potential_answer = self.llm.generate(prompt)
        if self.should_generate_message(potential_answer):
            return potential_answer
        else:
            return None

    def create_context_for_scheduler(self, potential_answer):
        pass  # TODO!!!

    def create_generation_prompt(self, message_history):
        pass  # TODO!!!
