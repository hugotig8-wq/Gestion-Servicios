from abc import ABC, abstractmethod


class BaseMetric(ABC):

    @abstractmethod
    def compute(self, model, *args, **kwargs) -> float:
        """
        Calcula la métrica y devuelve un valor entre 0 y 1.
        """
        pass
