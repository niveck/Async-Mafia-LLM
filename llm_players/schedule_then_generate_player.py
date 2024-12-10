from llm_players.llm_constants import turn_task_into_prompt, SCHEDULE_THEN_GENERATE_TYPE
from llm_players.llm_player import LLMPlayer
from llm_players.llm_wrapper import LLMWrapper


class ScheduleThenGeneratePlayer(LLMPlayer):

    TYPE_NAME = SCHEDULE_THEN_GENERATE_TYPE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # scheduler_kwargs = kwargs.get("scheduler_kwargs", kwargs)
        # self.scheduler = LLMWrapper(**scheduler_kwargs)
        self.scheduler = self.llm  # trying to use the same one for generation...

    def should_generate_message(self, message_history):
        prompt = self.create_scheduling_prompt(message_history)
        self.logger.log("prompt in should_generate_message", prompt)
        decision = self.scheduler.generate(prompt, self.get_system_info_message())
        self.logger.log("decision in should_generate_message", decision)
        return bool(decision) and self.pass_turn_token not in decision

    def generate_message(self, message_history):
        if self.should_generate_message(message_history):
            prompt = self.create_generation_prompt(message_history)
            self.logger.log("prompt in generate_message", prompt)
            return self.llm.generate(prompt, self.get_system_info_message())
        else:
            return ""

    def create_scheduling_prompt(self, message_history):
        # removed these because of too many talks:
        # "If one of the last messages has mentioned you, then choose to send a message now."
        task = f"Do you want to send a message to the group chat now, or do you prefer to wait " \
               f"for now and see what messages others will send? " \
               f"Remember to choose to send a message only if your contribution to the " \
               f"discussion in the current time will be meaningful enough - don't overflow the " \
               f"discussion with your messages! Pay attention to the amount of messages with " \
               f"your name compared to the amount of messages with names of other players " \
               f"and let them have their turn too! " \
               f"Check the speaker name in the last few messages, and decide accordingly based " \
               f"on whether you talked too much or not enough - " \
               f"make sure to say something every once in a while. " \
               f"Reply only with {self.use_turn_token} if you want to send a message now, " \
               f"or only with {self.pass_turn_token} if you want to wait for now, " \
               f"based on your decision! "
        return turn_task_into_prompt(task, message_history)

    def create_generation_prompt(self, message_history):
        task = f"Add a very short message to the game's chat. " \
               f"Be specific and keep it relevant to the current situation, " \
               f"according to the last messages and the game's status. " \
               f"Your message should only be one short sentence! " \
               f"Don't add a message that you've already added (in the chat history)! " \
               f"It is very important that you don't repeat yourself!"
        return turn_task_into_prompt(task, message_history)
