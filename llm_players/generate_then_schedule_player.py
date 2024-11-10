from llm_players.llm_constants import turn_task_into_prompt
from llm_players.llm_player import LLMPlayer
from llm_players.llm_wrapper import LLMWrapper


class GenerateThenSchedulePlayer(LLMPlayer):

    TYPE_NAME = "schedule_then_generate"

    def __init__(self, name, is_mafia, game_dir, **kwargs):
        super().__init__(name, is_mafia, game_dir, **kwargs)
        scheduler_kwargs = kwargs.get("scheduler_kwargs", kwargs)
        self.scheduler = LLMWrapper(**scheduler_kwargs)

    def should_generate_message(self, potential_message_and_message_history):
        # potential_message and message_history are combined because of parent class signature
        potential_message = potential_message_and_message_history[0]
        message_history = potential_message_and_message_history[1:]
        prompt = self.create_scheduling_prompt(potential_message, message_history)
        decision = self.scheduler.generate(prompt, self.get_system_info_message())
        return bool(decision) and self.pass_turn_token not in decision

    def generate_message(self, message_history):
        prompt = self.create_generation_prompt(message_history)
        potential_message = self.llm.generate(prompt, self.get_system_info_message())
        if self.should_generate_message([potential_message] + message_history):
            return potential_message
        else:
            return None

    def create_scheduling_prompt(self, potential_message, message_history):
        task = f"Here is a potential message you can send to the game's chat: " \
               f"{potential_message.strip()}\nDo you want to send this message to the game's " \
               f"chat now, or do you prefer to wait for now and see what messages others will " \
               f"send first? Remember to choose to send this message only if it's the best " \
               f"timing for it - remember you can always choose to send it later, but once " \
               f"you've decided to send it, there is not way back. Consider its contribution to " \
               f"the discussion in the current time. Don't overflow the discussion with your " \
               f"messages! Pay attention to the amount of messages with your name compared to " \
               f"the amount of messages with names of other players and let them have their turn " \
               f"too! Reply only with {self.use_turn_token} if you want to send this message " \
               f"now, or only with {self.pass_turn_token} if you want to wait for now, " \
               f"based on your decision! "
        return turn_task_into_prompt(task, message_history)

    def create_generation_prompt(self, message_history):  # TODO this is duplicate from schedule_then_generate... consider extracting? constant / parent class
        task = f"Add a short message to the game's chat. " \
               f"Your message should only be one sentence! "
        return turn_task_into_prompt(task, message_history)
