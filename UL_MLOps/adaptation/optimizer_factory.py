from typing import Iterable

import torch
from torch.optim import AdamW, SGD, Optimizer


class OptimizerFactory:
    """
    Construye optimizadores sin que el Trainer
    conozca su implementación.
    """

    @staticmethod
    def adamw(
        parameters: Iterable[torch.nn.Parameter],
        learning_rate: float,
        weight_decay: float = 0.01
    ) -> Optimizer:

        return AdamW(
            params=parameters,
            lr=learning_rate,
            weight_decay=weight_decay
        )

    @staticmethod
    def sgd(
        parameters: Iterable[torch.nn.Parameter],
        learning_rate: float,
        momentum: float = 0.9
    ) -> Optimizer:

        return SGD(
            params=parameters,
            lr=learning_rate,
            momentum=momentum
        )
