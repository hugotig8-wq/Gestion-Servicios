from dataclasses import dataclass


@dataclass(frozen=True)
class Config:

    model_revision: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    dataset_revision: str = "forget_v1"

    batch_size: int = 8

    max_length: int = 256

    learning_rate: float = 1e-4

    epochs: int = 5

    delta_threshold: float = 1.0

    checkpoint_dir: str = "checkpoints"

    log_dir: str = "logs"

    random_seed: int = 42
