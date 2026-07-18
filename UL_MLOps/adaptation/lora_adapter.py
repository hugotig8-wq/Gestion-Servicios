from typing import Iterable

import torch
from torch.optim import AdamW
from transformers import PreTrainedModel

from peft import (
    LoraConfig,
    TaskType,
    get_peft_model
)

from adaptation.parameter_strategy import ParameterStrategy


class LoRAStrategy(ParameterStrategy):

    def __init__(
        self,
        learning_rate: float = 5e-5,
        r: int = 8,
        alpha: int = 16, # Que no es la misma alpha de la funcion de perdida.
        dropout: float = 0.05
    ):

        self.learning_rate = learning_rate

        self.config = LoraConfig(

            task_type=TaskType.CAUSAL_LM,

            r=r,

            lora_alpha=alpha,

            lora_dropout=dropout,

            bias="none",

            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj"
            ]

        )

    def prepare_model(
        self,
        model: PreTrainedModel
    ) -> PreTrainedModel:

        model = get_peft_model(
            model,
            self.config
        )

        model.print_trainable_parameters()

        return model

    def trainable_parameters(
        self,
        model: PreTrainedModel
    ) -> Iterable[torch.nn.Parameter]:

        return filter(
            lambda parameter: parameter.requires_grad,
            model.parameters()
        )

    def save(

        self,

        model: PreTrainedModel,

        output_dir: str

    ):

        model.save_pretrained(output_dir)
