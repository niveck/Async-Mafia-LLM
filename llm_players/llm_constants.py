# DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
DEFAULT_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# prompts patterns:
INSTRUCTION_INPUT_RESPONSE_PATTERN = "instruction-input-response prompt pattern"
LLAMA3_PATTERN = "Llama 3 pattern"
DEFAULT_PROMPT_PATTERN = "default"
# generation hyper parameters:
MAX_NEW_TOKENS = 100  # TODO modify and don't forget to use
NUM_BEAMS = 4  # TODO modify and don't forget to use
# pipeline formats:
TEXT_GENERATION_TASK = "text-generation"
TASK2OUTPUT_FORMAT = {TEXT_GENERATION_TASK: "generated_text"}
# text constants:
INITIAL_GENERATION_PROMPT = ""  # TODO !!!
