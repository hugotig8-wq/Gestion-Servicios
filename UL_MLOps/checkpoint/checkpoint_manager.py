from pathlib import Path

from engine.validator import ValidationResult
from adaptation.parameter_strategy import ParameterStrategy
from config.experiment import Experiment

class CheckpointManager:

    def __init__(
        self,
        output_dir: str
    ):
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )
        self.best_score= float('-inf')

    def _score(self, result):
        if (result.fsr>=0.90 and 
            result.mu>=0.85 and 
            result.mia<=0.10
           ):
            return result.fsr+result.mu+result.fc-result.mia
        return float('-inf')
      
    def should_save(
        self,
        result: ValidationResult
    ) -> bool:

        return self._score(result)>self.best_score

    def save_checkpoint(

        self,

        strategy: ParameterStrategy,

        model,

        result,

        experiment: Experiment

    ):

        score= self._score(result)
        if score<=self.best_score:
            return

        self.best_score = score

        checkpoint_dir = (
            self.output_dir /
            f"epoch_{experiment.config.epoch}"
        )

        checkpoint_dir.mkdir(
            exist_ok=True
        )

        strategy.save(
            model,
            str(checkpoint_dir)
        )

        with open(
            checkpoint_dir / "metrics.txt",
            "w"
        ) as file:

            file.write(f"epoch={epoch}\n")
            file.write(f"fsr={result.fsr}\n")
            file.write(f"mu={result.mu}\n")
            file.write(f"fc={result.fc}\n")
            file.write(f"mia={result.mia}\n")
            file.write(f"score={score}\n")
