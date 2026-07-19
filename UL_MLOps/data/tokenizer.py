from transformers import AutoTokenizer


MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def build_tokenizer(model_name: str):

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    if tokenizer.pad_token is None:

        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    return tokenizer
