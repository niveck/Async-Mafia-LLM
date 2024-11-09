import os
import torch
from functools import cache
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoConfig, \
    pipeline
from game_constants import GENERAL_SYSTEM_INFO  # TODO: make sure this import doesnt lead to cyclic
from llm_players.llm_constants import DEFAULT_MODEL_NAME, TEXT_GENERATION_TASK, \
    TASK2OUTPUT_FORMAT, INITIAL_GENERATION_PROMPT, INSTRUCTION_INPUT_RESPONSE_PATTERN, \
    LLAMA3_PATTERN, DEFAULT_PROMPT_PATTERN, MAX_NEW_TOKENS, NUM_BEAMS


def is_local_path(model_name):
    return os.path.isdir(model_name)  # maybe should come up with better mechanism


@cache
def cached_model(model_name):
    if is_local_path(model_name):
        config = AutoConfig.from_pretrained(model_name)
        return AutoModelForSeq2SeqLM.from_pretrained(model_name, config=config)
    return AutoModelForCausalLM.from_pretrained(model_name)


@cache
def cached_tokenizer(model_name):
    return AutoTokenizer.from_pretrained(model_name)


@cache
def cached_pipeline(model_name, task):  # TODO: maybe use device as parameter?
    return pipeline(task, model_name, device_map="auto")


def log_model_choice(answer):  # TODO rewrite this function and use it in every possible way
    model_choices_logs_file = game_dir / "model_choices_logs.txt"
    if not model_choices_logs_file.exists():
        model_choices_logs_file.touch()
    log = "model chose to NOT generate..." if answer is None else "model chose to generate!"
    with open(model_choices_logs_file, "a") as f:
        f.write(f"[{time.strftime(TIME_FORMAT_FOR_TIMESTAMP)}] {log}\n")


class LLMWrapper:

    def __init__(self, **kwargs):
        self.model_name = kwargs.get("model_name", DEFAULT_MODEL_NAME)
        self.use_pipeline = kwargs.get("use_pipeline", False)
        self.pipeline_task = kwargs.get("pipeline_task", TEXT_GENERATION_TASK)
        self.max_new_tokens = kwargs.get("max_new_tokens", MAX_NEW_TOKENS)
        self.num_beams = kwargs.get("num_beams", NUM_BEAMS)
        self.device = torch.cuda.get_device_name() if torch.cuda.is_available() else "cpu"
        self.prompt_template = self._get_prompt_template()
        if self.use_pipeline:
            self.pipeline = cached_pipeline(self.model_name, self.pipeline_task)
            self.tokenizer = self.model = None
        else:
            self.pipeline = None
            self.tokenizer = cached_tokenizer(self.model_name)
            self.model = cached_model(self.model_name)
            self.model.to(self.device)
            self.model.eval()
        # initial generation just to save time of first generation in real time
        self.generate(INITIAL_GENERATION_PROMPT, system_info=GENERAL_SYSTEM_INFO)

    def _get_prompt_template(self):
        model_name = self.model_name.lower()
        if "phi-3" in model_name:
            return INSTRUCTION_INPUT_RESPONSE_PATTERN
        elif "llama-3" in model_name:
            return LLAMA3_PATTERN
        # elif  # TODO: add an option for the fine-tuned model based on the name I saved it by!
        # elif "____" in model_name: return "____"
        else:
            return DEFAULT_PROMPT_PATTERN

    def pipeline_preprocessing(self, input_text, system_info):
        if self.prompt_template in (INSTRUCTION_INPUT_RESPONSE_PATTERN, LLAMA3_PATTERN):
            # TODO: validate that both these model templates support this kind of pipeline
            system_message = [{"role": "system", "content": system_info}] if system_info else []
            return system_message + [{"role": "user", "content": input_text}]
        else:
            raise NotImplementedError("Used model doesn't support pipeline, "
                                      "try `use_pipeline=False` in config")

    def direct_preprocessing(self, input_text, system_info) -> str:
        # TODO: make sure system info is produced with space at the end
        if self.prompt_template == INSTRUCTION_INPUT_RESPONSE_PATTERN:
            return f"### Instruction:\n{system_info + input_text}\n### Response: "
        # elif self.prompt_template is of Phi-3 style:
            # return f"<|user|>{input_text}<|end|>\n<|assistant|>"
        elif self.prompt_template == LLAMA3_PATTERN:
            if system_info:
                system_prompt = f"<|start_header_id|>system<|end_header_id|>{system_info}<|eot_id|>"
            else:
                system_prompt = ""
            return f"<|begin_of_text|>{system_prompt}" \
                   f"<|start_header_id|>user<|end_header_id|>{input_text}<|eot_id|>" \
                   f"<|start_header_id|>assistant<|end_header_id|>"
        # elif  # TODO: add an option for the fine-tuned model based on its training format!
        else:
            raise NotImplementedError("Missing prompt template for used model")

    def direct_postprocessing(self, decoded_output):
        if self.prompt_template == INSTRUCTION_INPUT_RESPONSE_PATTERN:
            output = decoded_output.split("### Response:")[1].strip().split("</s>")[0]
            # TODO: following lines are a reminder from SAUCE - debug to see if needed
            # output = output.removeprefix(f"{self.name}: ")
            # time_and_name_prefix = f"] {self.name}: "
            # if time_and_name_prefix in output:
            #     output = output.split(time_and_name_prefix)[1]
            return output.strip()
        elif self.prompt_template == LLAMA3_PATTERN:
            assistant_prefix = "<|start_header_id|>assistant<|end_header_id|>"
            if assistant_prefix in decoded_output:
                decoded_output = decoded_output.split(assistant_prefix)[1]
            return decoded_output.split("<|eot_id|>")[0].strip()
        # elif  # TODO: add an option for the fine-tuned model based on its training format!
        else:
            raise NotImplementedError("Missing output template for used model")

    def generate(self, input_text, system_info=""):
        with torch.inference_mode():
            if self.use_pipeline:
                messages = self.pipeline_preprocessing(input_text, system_info)
                outputs = self.pipeline(messages)  # TODO maybe use max_new_tokens=self.max_new_tokens  # TODO maybe also use num_beams?
                final_output = outputs[0][TASK2OUTPUT_FORMAT[self.pipeline_task]][-1]
            else:
                prompt = self.direct_preprocessing(input_text, system_info)
                inputs = self.tokenizer(prompt, return_tensors="pt")
                inputs = {key: value.to(self.device) for key, value in inputs.items()}
                outputs = self.model.generate(**inputs,
                                              # max_length=self.max_source_length,
                                              max_new_tokens=self.max_new_tokens,
                                              num_beams=self.num_beams,
                                              )
                decoded_output = self.tokenizer.decode(outputs[0])
                final_output = self.direct_postprocessing(decoded_output)
        return final_output.strip()
