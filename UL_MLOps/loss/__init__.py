from .base_loss import BaseLoss
from .unlearning_loss import UnlearningLoss

__all__ = [
    "BaseLoss",
    "UnlearningLoss",
]

#Determina qué es público
#from loss import * sólo importa lo que esté en __all__
