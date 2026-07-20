from abc import ABC, abstractmethod
from typing import Iterable

import torch
from transformers import PreTrainedModel


class ParameterStrategy(ABC):
    """
    Interfaz base para cualquier estrategia de actualización de parámetros.

    El Trainer nunca debe conocer si el modelo utiliza:

        - LoRA
        - QLoRA
        - Full Fine Tuning
        - Capas congeladas
        - Otra estrategia futura

    Solamente conoce esta interfaz.
    """

    @abstractmethod
    def prepare_model(
        self,
        model: PreTrainedModel
    ) -> PreTrainedModel:
        """
        Modifica el modelo antes del entrenamiento.

        Ejemplos:

            - Congelar parámetros
            - Añadir adaptadores LoRA
            - Insertar nuevas capas
            - Preparar cuantización

        Devuelve el modelo listo para entrenar.
        """
        pass

    @abstractmethod
    def trainable_parameters(
        self,
        model: PreTrainedModel
    ) -> Iterable[torch.nn.Parameter]:
        """
        Devuelve únicamente los parámetros
        que el optimizador debe actualizar.
        """
        pass
        

    @abstractmethod
    def save(
        self,
        model: PreTrainedModel,
        output_dir: str
    ) -> None:
        """
        Guarda únicamente aquello que
        pertenece a esta estrategia.

        Ejemplos:

            LoRA:
                guarda únicamente adapters

            Full Fine Tuning:
                guarda todo el modelo
        """
        pass
