from game_constants import REMAINING_PLAYERS_FILE, GAME_MANAGER_NAME, MESSAGE_PARSING_PATTERN
from llm_players.llm_constants import turn_task_into_prompt, EVERY_X_MESSAGES_TYPE, \
    make_more_human_like
from llm_players.llm_player import LLMPlayer


class EveryXMessagesPlayer(LLMPlayer):  # TODO implement this!

    TYPE_NAME = EVERY_X_MESSAGES_TYPE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TODO implement!
        # self.every_x = number_of_active_players?...
        # # scheduler_kwargs = kwargs.get("scheduler_kwargs", kwargs)
        # # self.scheduler = LLMWrapper(**scheduler_kwargs)
        # self.scheduler = self.llm  # trying to use the same one for generation...

    def should_generate_message(self, message_history):
        pass
        # TODO implement!
        # TODO don't forget to log everything!
        # if no_one_has_talked_yet_in_current_phase(message_history):
        #     return False
        # prompt = self.create_scheduling_prompt(message_history)
        # self.logger.log("prompt in should_generate_message", prompt)
        # decision = self.scheduler.generate(prompt, self.get_system_info_message())
        # self.logger.log("decision in should_generate_message", decision)
        # return bool(decision) and self.pass_turn_token not in decision

    def generate_message(self, message_history):
        if self.should_generate_message(message_history):
            prompt = self.create_generation_prompt(message_history)
            self.logger.log("prompt in generate_message", prompt)
            message = self.llm.generate(prompt, self.get_system_info_message())
            message = make_more_human_like(message)
            return message
        else:
            return ""

    def create_generation_prompt(self, message_history):
        # TODO: should be constant?
        task = f"Add a very short message to the game's chat. " \
               f"Be specific and keep it relevant to the current situation, " \
               f"according to the last messages and the game's status. " \
               f"Your message should only be one short sentence! " \
               f"Don't add a message that you've already added (in the chat history)! " \
               f"It is very important that you don't repeat yourself! " \
               f"Match your style of message to the other player's message style, " \
               f"with more emphasis on more recent messages.\n" \
               f"Here are some examples of possible messages from a hypothetical game's chat, " \
               f"as style inspiration:\n" \
               f"\"I'm telling you guys, we can't trust Joseph\",\n" \
               f"\"Jessica is sus\",\n" \
               f"\"i think it is phoebe, she knew that diane was mafia and she tried to blame someone else\",\n" \
               f"\"John is probably mafia, diane was mafia and voted for lindsay who voted for john\",\n" \
               f"\"John is out tho\",\n" \
               f"\"i figured out diane is mafia\",\n" \
               f"\"jennifer is the mafia for sure! she didn't vote with us\",\n" \
               f"\"why would i kill mafia if i was mafia ?\",\n" \
               f"\"Jennifer is too quiet\",\n" \
               f"\"they only try to gain our trust\",\n" \
               f"\"exactly\",\n" \
               f"\"because they are the only one that didnt vote diane\",\n" \
               f"\"i think Moe is so loud\",\n" \
               f"\"jennifer, do you have anything to say for yourself?\"...\n"
        return turn_task_into_prompt(task, message_history)
