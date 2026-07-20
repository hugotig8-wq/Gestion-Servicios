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
        if score<=experiment.best_score:
            return

        experiment.best_score = score

        checkpoint_dir = (

            Path(

                experiment.config.checkpoint_dir

            )

            /

            experiment.experiment_id

        )

        checkpoint_dir.mkdir(

            parents=True,

            exist_ok=True

        )

        checkpoint_path = (

            checkpoint_dir

            /

            f"{CheckpointType.BEST.value}.pt"

        )

        torch.save(

            {

                "epoch":

                    experiment.current_epoch,

                "score":

                    score,

                "experiment_id":

                    experiment.experiment_id,

                "status":

                    experiment.status.value,

                "model_state_dict":

                    strategy.get_state_dict(model),

                "config":

                    experiment.config

            },

            checkpoint_path

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
