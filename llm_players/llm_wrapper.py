import os
import torch
from functools import cache
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoConfig, \
    pipeline
from llm_players.llm_constants import DEFAULT_MODEL_NAME, TEXT_GENERATION_TASK, TASK2OUTPUT_FORMAT, INITIAL_GENERATION_PROMPT


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
def cached_pipeline(model_name, task):
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
        self.device = torch.cuda.get_device_name() if torch.cuda.is_available() else "cpu"
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
        self.generate(INITIAL_GENERATION_PROMPT)  # TODO write this INITIAL_GENERATION_PROMPT

    def generate(self, input_text):
        with torch.inference_mode():
            if self.use_pipeline:
                outputs = self.pipeline(messages)  # TODO: [{"role": "system", "content": "..."}, {"role": "user", "content": input_text...}]  # TODO maybe use max_new_tokens=self.max_new_tokens  # TODO maybe also use num_beams?
                final_output = outputs[0][TASK2OUTPUT_FORMAT[self.pipeline_task]][-1]
            else:
                inputs = self.tokenizer(input_text, return_tensors="pt")
                inputs = {key: value.to(self.device) for key, value in inputs.items()}
                outputs = self.model.generate(**inputs,
                                              # max_length=self.max_source_length,
                                              num_beams=self.num_beams,
                                              max_new_tokens=self.max_new_tokens,
                                              )
                final_output = self.tokenizer.decode(outputs[0])
        return final_output.strip()
