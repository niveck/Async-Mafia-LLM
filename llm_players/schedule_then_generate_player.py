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

    def create_context_for_scheduler(self, message_history):
        task = f"Do you want to speak now and add to the discussion, " \
               f"or do you prefer to wait for now and see what others will say? " \
               f"Remember to choose to speak only if your contribution to the discussion " \
               f"in the current time will be meaningful enough - don't overflow the discussion " \
               f"with your messages! Pay attention to the amount of messages with your name " \
               f"compared to the amount of messages with names of other players " \
               f"and let them have their turn too! " \
               f"Reply only {self.use_turn_token} or {self.pass_turn_token} " \
               f"based on your decision!"
        return self._create_prompt_skeleton(experiment_scenario, chat_list, task)

    def create_generation_prompt(self, message_history):
        pass  # TODO!!!
