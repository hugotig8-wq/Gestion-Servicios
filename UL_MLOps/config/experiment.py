from dataclasses import dataclass, field
from datetime import datetime
import uuid
from config.experiment_status import ExperimentStatus

from config.config import Config
import torch


@dataclass
class Experiment:

    config: Config

    experiment_id: str

    device: torch.device

    started_at: datetime

    ended_at: datetime | None

    status: str

    best_score: float

    current_epoch: int
    
    def __post_init__(self):

        self.started_at = datetime.utcnow()

        timestamp = self.started_at.strftime(
            "%Y%m%d_%H%M%S"
        )

        random_id = uuid.uuid4().hex[:8]

        self.experiment_id = f"{timestamp}_{random_id}"
