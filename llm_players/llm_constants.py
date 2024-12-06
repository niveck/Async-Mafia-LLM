from game_constants import get_current_timestamp

# DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
DEFAULT_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# prompts patterns:
INSTRUCTION_INPUT_RESPONSE_PATTERN = "instruction-input-response prompt pattern"
LLAMA3_PATTERN = "Llama 3 pattern"
DEFAULT_PROMPT_PATTERN = "default"
# generation hyper parameters:
MAX_NEW_TOKENS = 100
NUM_BEAMS = 4
# pipeline formats:
TEXT_GENERATION_TASK = "text-generation"
TASK2OUTPUT_FORMAT = {TEXT_GENERATION_TASK: "generated_text"}
# text constants:
INITIAL_GENERATION_PROMPT = "Do you understand the rules?"


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
