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

        self.mean_epoch_total_loss = 0

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

            validation_result = self.validator.validate(

                self.trainer.model,

                retain_loader,

                forget_loader,

                validation_loader

            )

            self.logger.log(

                epoch,

                last_train_result,

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
