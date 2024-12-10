from game_constants import get_current_timestamp, RULES_OF_THE_GAME

MODEL_NAMES = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "microsoft/Phi-3-mini-4k-instruct"
]
DEFAULT_MODEL_NAME = MODEL_NAMES[0]

# prompts patterns:
INSTRUCTION_INPUT_RESPONSE_PATTERN = "instruction-input-response prompt pattern"
LLAMA3_PATTERN = "Llama 3 pattern"
DEFAULT_PROMPT_PATTERN = "default"

# generation hyper parameters:
DEFAULT_MAX_NEW_TOKENS = 100
DEFAULT_NUM_BEAMS = 4

DEFAULT_NUM_WORDS_PER_SECOND_TO_WAIT = 3  # simulates number of words written normally per second

# pipeline formats:
TEXT_GENERATION_TASK = "text-generation"
TASK2OUTPUT_FORMAT = {TEXT_GENERATION_TASK: "generated_text"}

# text constants:
INITIAL_GENERATION_PROMPT = "Do you understand the rules?"
PASS_TURN_TOKEN_OPTIONS = ["<wait>", "<pass>", "<quiet>", "[[wait]]", "[[pass]]", "[[quiet]]"]
USE_TURN_TOKEN_OPTIONS = ["<send>", "<speak>", "<use>", "[[send]]", "[[speak]]", "[[use]]"]
DEFAULT_PASS_TURN_TOKEN = PASS_TURN_TOKEN_OPTIONS[0]
DEFAULT_USE_TURN_TOKEN = USE_TURN_TOKEN_OPTIONS[0]
GENERAL_SYSTEM_INFO = f"You are a bot player in an online version of the party game Mafia. " \
                      f"You have an outgoing personality, and you like to participate in games, " \
                      f"but you also don't want everyone to have their eyes on you all the time.\n" \
                      f"The rules of the game: {RULES_OF_THE_GAME}"
# I removed the following because it didn't choose to wait: "You have a very outgoing personality"

# LLM players type names:
SCHEDULE_THEN_GENERATE_TYPE = "schedule_then_generate"
GENERATE_THEN_SCHEDULE_TYPE = "generate_then_schedule"
FINE_TUNED_TYPE = "fine_tuned"
ASYNC_TYPES = [SCHEDULE_THEN_GENERATE_TYPE, GENERATE_THEN_SCHEDULE_TYPE, FINE_TUNED_TYPE]
DEFAULT_ASYNC_TYPE = ASYNC_TYPES[0]

# config keys:
LLM_CONFIG_KEY = "llm_config"  # should match the key in PlayerConfig dataclass
GAME_DIR_KEY = "game_dir"  # should match key word in LLMPlayer
MODEL_NAME_KEY = "model_name"
USE_PIPELINE_KEY = "use_pipeline"
PIPELINE_TASK_KEY = "pipeline_task"
MAX_NEW_TOKENS_KEY = "max_new_tokens"
NUM_BEAMS_KEY = "num_beams"
WORDS_PER_SECOND_WAITING_KEY = "num_words_per_second_to_wait"
PASS_TURN_TOKEN_KEY = "pass_turn_token"
USE_TURN_TOKEN_KEY = "use_turn_token"
ASYNC_TYPE_KEY = "async_type"

INT_CONFIG_KEYS = [MAX_NEW_TOKENS_KEY, NUM_BEAMS_KEY, WORDS_PER_SECOND_WAITING_KEY]
BOOL_CONFIG_KEYS = [USE_PIPELINE_KEY]

DEFAULT_LLM_CONFIG = {
    MODEL_NAME_KEY: DEFAULT_MODEL_NAME,
    USE_PIPELINE_KEY: False,
    PIPELINE_TASK_KEY: TEXT_GENERATION_TASK,
    MAX_NEW_TOKENS_KEY: DEFAULT_MAX_NEW_TOKENS,
    NUM_BEAMS_KEY: DEFAULT_NUM_BEAMS,
    WORDS_PER_SECOND_WAITING_KEY: DEFAULT_NUM_WORDS_PER_SECOND_TO_WAIT,
    PASS_TURN_TOKEN_KEY: DEFAULT_PASS_TURN_TOKEN,
    USE_TURN_TOKEN_KEY: DEFAULT_USE_TURN_TOKEN,
    ASYNC_TYPE_KEY: DEFAULT_ASYNC_TYPE
}

LLM_CONFIG_KEYS_OPTIONS = {
    MODEL_NAME_KEY: MODEL_NAMES,
    PIPELINE_TASK_KEY: [TEXT_GENERATION_TASK],
    PASS_TURN_TOKEN_KEY: PASS_TURN_TOKEN_OPTIONS,
    USE_TURN_TOKEN_KEY: USE_TURN_TOKEN_OPTIONS,
    ASYNC_TYPE_KEY: ASYNC_TYPES
}


def turn_task_into_prompt(task, message_history):
    prompt = f"The current time is [{get_current_timestamp()}].\n"
    if not message_history:
        prompt += "No player has sent a message yet.\n"
    else:
        prompt = "Here is the message history so far, including [timestamps]:\n"
        prompt += "".join(message_history)  # each one already ends with "\n"
    prompt += task.strip() + " "  # validates a " " is added before the next instruction
    # not necessarily needed with all models, seemed relevant to Llama3.1:
    prompt += "Don't add the time, the timestamp or the [timestamp] in your answer!\n"
    return prompt
