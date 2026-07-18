from dataclasses import dataclass
from typing import Dict

import torch
from torch.nn import Module
from torch.optim import Optimizer


@dataclass
class TrainStepResult:
    """
    Resultado de un paso de entrenamiento.
    """

    total_loss: float
    retain_loss: float
    forget_loss: float


class Trainer:

    def __init__(
        self,
        model: Module,
        optimizer: Optimizer,
        loss_function # Si mas adelante quiero probar otra forma de UL simplemente cambio la implementación de loss_function
    ):

        self.model = model
        self.optimizer = optimizer
        self.loss_function = loss_function

    def train_step(
        self,
        retain_batch: Dict,
        forget_batch: Dict
    ) -> TrainStepResult:

        self.model.train()

        self.optimizer.zero_grad()

        retain_outputs = self.model(
            input_ids=retain_batch["input_ids"],
            attention_mask=retain_batch["attention_mask"],
            labels=retain_batch["labels"]
        )

        forget_outputs = self.model(
            input_ids=forget_batch["input_ids"],
            attention_mask=forget_batch["attention_mask"],
            labels=forget_batch["labels"]
        )

        total_loss, retain_loss, forget_loss = self.loss_function.compute(
            retain_outputs.logits,
            forget_outputs.logits,
            retain_labels,
            forget_labels
        )

        total_loss.backward()

        self.optimizer.step()

        return TrainStepResult(

            total_loss=float(total_loss.item()),

            retain_loss=float(retain_loss.item()),

            forget_loss=float(forget_loss.item())

        )
