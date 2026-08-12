from dataclasses import dataclass, field
from datetime import datetime
import uuid
from config.config import Config
from config.experiment_status import ExperimentStatus
import torch


@dataclass
class Experiment:

    config: Config
    
    device: torch.device | None = None

    experiment_id: str = field(init=False)

    started_at: datetime = field(init=False)

    ended_at: datetime | None = None

    current_epoch: int = 0

    best_score: float = float("-inf")

    status: ExperimentStatus = ExperimentStatus.CREATED

    def __post_init__(self):

        self.started_at = datetime.utcnow()

        timestamp = self.started_at.strftime(
            "%Y%m%d_%H%M%S"
        )

        random_id = uuid.uuid4().hex[:8]

        self.experiment_id = f"{timestamp}_{random_id}"
