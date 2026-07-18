from dataclasses import dataclass
from typing import Optional

@dataclass
class UnlearningConfig:
    """
    Cao & Yang (2015), Cap. 6 - Experimental Setup
    """
    
    # Coeficientes de loss (Cao & Yang, Sec. 4.3)
    alpha: float = 1.0      # Peso de Retain Loss
    beta: float = 1.0       # Peso de Forget Loss
    gamma: float = 0.1      # Peso de regularización
    
    # Tamaños de batch
    retain_batch_size: int = 32
    forget_batch_size: int = 8
    
    # Hiperparámetros de entrenamiento
    learning_rate: float = 5e-5
    num_unlearning_epochs: int = 5
    warmup_steps: int = 500
    weight_decay: float = 0.01
    
    # Validación (Cao & Yang, Cap. 6)
    validation_interval: int = 500      # Validar cada N pasos
    fsr_threshold: float = 0.9          # Forget Success Rate mínimo
    utility_threshold: float = 0.95     # Model Utility mínimo
    
    # Device
    device: str = "cuda"
    mixed_precision: str = "fp16"
