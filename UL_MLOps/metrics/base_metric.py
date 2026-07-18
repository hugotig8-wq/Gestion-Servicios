from abc import ABC, abstractmethod


class BaseMetric(ABC):

    @abstractmethod
    def compute(self, model, *args, **kwargs) -> float:
    # *args, **kwargs se encarga de usar sólo lo necesario
    #Si definimos compute con todas las metricas sobrarían en cada cual.
        """
        Calcula la métrica y devuelve un valor entre 0 y 1.
        """
        pass
