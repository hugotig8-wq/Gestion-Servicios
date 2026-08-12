from dataclasses import dataclass

import torch


@dataclass
class FCResult:

    total_samples: int

    consistent_samples: int

    fc: float


class ForgetQuality:

    def __init__(

        self,

        tokenizer,

        device: str = "cpu",

        max_new_tokens: int = 64

    ):

        self.tokenizer = tokenizer

        self.device = device

        self.max_new_tokens = max_new_tokens

    def compute(

        self,

        model_before,

        model_after,

        prompts: list[str]

    ) -> FCResult:

        if not prompts:

            raise ValueError(

                "prompts cannot be empty."

            )

        model_before.eval()

        model_after.eval()

        consistent_samples = 0

        with torch.no_grad():

            for prompt in prompts:

                answer_before = self._generate(

                    model_before,

                    prompt

                )

                answer_after = self._generate(

                    model_after,

                    prompt

                )

                if self._normalize(

                    answer_before

                ) == self._normalize(

                    answer_after

                ):

                    consistent_samples += 1

        total_samples = len(prompts)

        fc = (

            consistent_samples

            /

            total_samples

        )

        return FCResult(

            total_samples=total_samples,

            consistent_samples=consistent_samples,

            fc=fc

        )

    def _generate(

        self,

        model,

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

        outputs = model.generate(

            **inputs,

            max_new_tokens=self.max_new_tokens,

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

    def _normalize(

        self,

        text: str

    ) -> str:

        return " ".join(

            text.lower().split()

        )
