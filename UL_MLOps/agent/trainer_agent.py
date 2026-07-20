from itertools import zip_longest

from engine.trainer import Trainer
from engine.validator import Validator
from checkpoint.checkpoint_manager import CheckpointManager
from logging.experiment_logger import ExperimentLogger
from engine.trainer import TrainStepResult
from tqdm import tqdm


class TrainerAgent:

    def __init__(
        self,
        trainer: Trainer,
        validator: Validator,
        checkpoint_manager: CheckpointManager,
        logger: ExperimentLogger,
        strategy
    ):

        self.trainer = trainer

        self.validator = validator

        self.checkpoint_manager = checkpoint_manager

        self.logger = logger

        self.strategy = strategy


    def train(

        self,

        experiment,

        retain_loader,

        forget_loader,

        validation_loader

    ):

        epochs_progress = tqdm(
            range(experiment.config.epochs),
            desc="Training"
        )

        for epoch in epochs_progress:
            
            total_loss = 0.0

            retain_loss = 0.0

            forget_loss = 0.0

            num_batches = 0

            experiment.current_epoch = epoch +1

            batches_progress = tqdm(
                zip_longest(
                    retain_loader,
                    forget_loader,
                    fillvalue=None
                ),
                total=min(
                    len(retain_loader),
                    len(forget_loader)
                ),
                desc=f"Epoch {epoch + 1}",
                leave=False
            )

            last_train_result = None

            for retain_batch, forget_batch in batches_progress :

                if retain_batch is None or forget_batch is None:
                    break

                last_train_result = self.trainer.train_step(

                    retain_batch,

                    forget_batch

                )

                total_loss += last_train_result.total_loss
                retain_loss += last_train_result.retain_loss
                forget_loss += last_train_result.forget_loss
                num_batches += 1

                batches_progress.set_postfix(
                    loss=f"{last_train_result.total_loss:.3f}",
                    retain=f"{last_train_result.retain_loss:.3f}",
                    forget=f"{last_train_result.forget_loss:.3f}"
                )

                
            mean_train_result = TrainStepResult(
                total_loss=total_loss / num_batches,
                retain_loss=retain_loss / num_batches,
                forget_loss=forget_loss / num_batches,
            )

            validation_result = self.validator.validate(

                self.trainer.model,

                retain_loader,

                forget_loader,

                validation_loader

            )

            self.logger.log(

                epoch,

                mean_train_result,

                validation_result

            )

            if self.checkpoint_manager.should_save(

                validation_result

            ):

                self.checkpoint_manager.save_checkpoint(

                    experiment = experiment,

                    strategy= strategy,

                    model= model,

                    result = validation_result,

                )

        experiment.status = ExperimentStatus.FINISHED

        experiment.ended_at = datetime.utcnow()
        
        self.logger.save()
