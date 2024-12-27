from game_constants import REMAINING_PLAYERS_FILE, GAME_MANAGER_NAME
from llm_players.llm_constants import turn_task_into_prompt, SCHEDULE_THEN_GENERATE_TYPE, \
    make_more_human_like
from llm_players.llm_player import LLMPlayer
from llm_players.llm_wrapper import LLMWrapper

TALKATIVE_VERSION = "Make sure to say something every once in a while, and make yourself heard. " \
                    "Remember you like to be active in the game, so participate and be " \
                    "as talkative as other players! "  # TODO better const name + move to consts file!
QUIETER_VERSION = "Don't overflow the discussion with your messages! " \
                  "Pay attention to the amount of messages with your name compared to the amount " \
                  "of messages with names of other players and let them have their turn too! " \
                  "Check the speaker name in the last few messages, and decide accordingly " \
                  "based on whether you talked too much. "  # TODO better const name + move to consts file!


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
            message = self.llm.generate(prompt, self.get_system_info_message())
            message = make_more_human_like(message)
            return message
        else:
            return ""

    def talkative_scheduling_prompt_modifier(self, message_history):
        if not message_history:
            return TALKATIVE_VERSION
        all_players = (self.game_dir / REMAINING_PLAYERS_FILE).read_text().splitlines()
        players_counts = {player: 0 for player in all_players}
        for message in message_history[::-1]:
            if f"] {GAME_MANAGER_NAME}: " in message and "voted for" in message:  # TODO constants!
                continue
            elif f"] {GAME_MANAGER_NAME}: " in message and "has ended, now it's time to vote!" in message:  # TODO constants!
                break
            for player in players_counts:
                if f"] {player}: " in message:  # TODO constants!
                    players_counts[player] += 1
        all_player_messages = sum(players_counts.values())
        if not all_player_messages or players_counts[self.name] / all_player_messages < 1 / len(all_players):
            return TALKATIVE_VERSION
        else:
            return QUIETER_VERSION

    def create_scheduling_prompt(self, message_history):
        # removed these because of too many talks:
        # "If one of the last messages has mentioned you, then choose to send a message now."
        task = f"Do you want to send a message to the group chat now, or do you prefer to wait " \
               f"for now and see what messages others will send? " \
               f"Remember to choose to send a message only if your contribution to the " \
               f"discussion in the current time will be meaningful enough. " \
               f"{self.talkative_scheduling_prompt_modifier(message_history).strip()} " \
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
