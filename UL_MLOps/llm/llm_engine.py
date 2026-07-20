from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)

import torch


class LLMEngine:

    def __init__(

        self,

        model_name: str,

        device: str | None = None,

        max_new_tokens: int = 512

    ):

        self.device = (

            device

            if device is not None

            else (

                "cuda"

                if torch.cuda.is_available()

                else "cpu"

            )

        )

        self.max_new_tokens = max_new_tokens

        self.tokenizer = AutoTokenizer.from_pretrained(

            model_name

        )

        self.model = AutoModelForCausalLM.from_pretrained(

            model_name

        ).to(

            self.device

        )

        self.model.eval()

    def generate(

        self,

        prompt: str

    ) -> str:

        inputs = self.tokenizer(

            prompt,

            return_tensors="pt",

            truncation=True,

            max_length=2048

        )

        inputs = {

            key: value.to(

                self.device

            )

            for key, value

            in inputs.items()

        }

        with torch.no_grad():

            outputs = self.model.generate(

                **inputs,

                max_new_tokens=self.max_new_tokens,

                temperature=0.2,

                top_p=0.95,

                repetition_penalty=1.1,

                do_sample=False,

                eos_token_id=self.tokenizer.eos_token_id,

                pad_token_id=self.tokenizer.eos_token_id

            )

        generated_tokens = outputs[0][

            inputs["input_ids"].shape[1]:

        ]

        return self.tokenizer.decode(

            generated_tokens,

            skip_special_tokens=True

        ).strip()
