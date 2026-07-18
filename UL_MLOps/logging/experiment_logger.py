import json
from pathlib import Path
from typing import List, Dict

from engine.trainer import TrainStepResult
from engine.validator import ValidationResult


class ExperimentLogger:

    def __init__(
        self,
        output_dir: str
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.history: List[Dict] = []

    def log(

        self,

        epoch: int,

        train_result: TrainStepResult,

        validation_result: ValidationResult

    ):

        record = {

            "epoch": epoch,

            "total_loss": train_result.total_loss,

            "retain_loss": train_result.retain_loss,

            "forget_loss": train_result.forget_loss,

            "fsr": validation_result.fsr,

            "mu": validation_result.mu,

            "fc": validation_result.fc,

            "mia": validation_result.mia

        }

        self.history.append(record)

    def save(self):

        output_file = self.output_dir / "experiment.json"

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(

                self.history,

                file,

                indent=4

        )
