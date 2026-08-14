from dataclasses import dataclass

@dataclass
class TrainingSnapshot:

    epoch: int

    train_loss: float

    validation_loss: float

    learning_rate: float

    elapsed_seconds: float

    fsr: float

    mu: float

    fc: float

    mia: float
