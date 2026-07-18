from dataclasses import dataclass
from typing import Optional

@dataclass
class UnlearningConfig:
    """
    Configuración para Machine Unlearning en TinyLlama-1.1B
    Referencia: Cao & Yang (2015), Cap. 6 - Experimental Setup
    
    Optimizado para Codespace con recursos limitados
    """
    
    # Modelo
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    # Coeficientes de loss (Cao & Yang, Sec. 4.3)
    alpha: float = 1.0      # Peso de Retain Loss
    beta: float = 1.0       # Peso de Forget Loss  
    gamma: float = 0.1      # Peso de regularización L2
    
    # Tamaños de batch (pequeños para Codespace)
    retain_batch_size: int = 4
    forget_batch_size: int = 2
    
    # Hiperparámetros de entrenamiento
    learning_rate: float = 5e-5
    num_unlearning_epochs: int = 1
    warmup_steps: int = 50
    weight_decay: float = 0.01
    
    # Validación (Cao & Yang, Cap. 6)
    validation_interval: int = 50
    fsr_threshold: float = 0.9          # Forget Success Rate mínimo
    utility_threshold: float = 0.95     # Model Utility mínimo
    fc_threshold: float = 0.1           # Forgetting Consistency máximo
    
    # Device y precision
    device: str = "cpu"
    use_half_precision: bool = False    # Float32 en CPU
    
    # Secuencia
    max_seq_length: int = 128
    
    # Logging
    log_interval: int = 10
    save_interval: int = 100
