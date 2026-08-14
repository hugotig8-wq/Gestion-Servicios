from pathlib import Path

from engine.validator import ValidationResult
from adaptation.parameter_strategy import ParameterStrategy
from config.experiment import Experiment

import torch

from training.training_snapshot import TrainingSnapshot


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

    def _score(self, snapshot:TrainingSnapshot):
        if (snapshot.fsr>=0.90 and 
            snapshot.mu>=0.85 and 
            snapshot.mia<=0.10
           ):
            return snapshot.fsr+snapshot.mu+snapshot.fc-snapshot.mia
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

        optimizer,

        snapshot: TraininhSnapshot,

        experiment: Experiment

    ):

        score= self._score(snapshot)
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
        
        strategy.save(
            model,
            str(checkpoint_dir)
        )

        torch.save(

            {

                "epoch":

                    snapshot.epoch,

                "best_score":

                    experiment.best_score,

                "train_loss":

                    snapshot.train_loss,
                
                "learning_rate":

                    snapshot.learning_rate,

                "experiment_id":

                    experiment.experiment_id,

                "status":

                    experiment.status.value,

                 "metrics": {

                    "fsr":

                        snapshot.fsr,

                    "mu":

                        snapshot.mu,

                    "fc":

                        snapshot.fc,

                    "mia":

                        snapshot.mia

                },

                "optimizer_state_dict":# luegi resume_training para restaurar el estado del optimizador
                
                    optimizer.state_dict(),

                "model_state_dict":

                    strategy.get_state_dict(model),

                "config":

                    experiment.config.__dict__

            },

            checkpoint_dir

            /

            "training_state.pt"

        )

        

