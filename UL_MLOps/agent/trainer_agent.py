from itertools import zip_longest

from engine.trainer import Trainer
from engine.validator import Validator
from checkpoint.checkpoint_manager import CheckpointManager
from logging.experiment_logger import ExperimentLogger


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

        self.mean_epoch_total_loss = 0.0

        self.mean_epoch_retain_loss = 0.0

        self.mean_epoch_forget_loss = 0.0

        self.num_batches = 0

        self.mean_train_result

    def train(

        self,

        epochs,

        retain_loader,

        forget_loader,

        validation_loader

    ):

        for epoch in range(epochs):

            last_train_result = None

            for retain_batch, forget_batch in zip_longest(

                retain_loader,

                forget_loader,

                fillvalue=None

            ):

                if retain_batch is None or forget_batch is None:
                    break

                last_train_result = self.trainer.train_step(

                    retain_batch,

                    forget_batch

                )

                self.mean_epoch_total_loss += last_train_result.total_loss
                self.mean_epoch_retain_loss += last_train_result.retain_loss
                self.mean_epoch_forget_loss += last_train_result.forget_loss
                self.num_batches += 1
                
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

                    self.strategy,

                    self.trainer.model,

                    validation_result,

                    epoch

                )

        self.logger.save()
