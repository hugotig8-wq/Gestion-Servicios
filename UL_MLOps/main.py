from transformers import AutoModelForCausalLM

from adaptation.lora_adapter import LoRAStrategy
from adaptation.optimizer_factory import OptimizerFactory

from checkpoint.checkpoint_manager import CheckpointManager

from engine.trainer import Trainer
from engine.validator import Validator

from logging.experiment_logger import ExperimentLogger

from agent.trainer_agent import TrainerAgent

from metrics.fsr import ForgetSuccessRate
from metrics.mu import ModelUtility
from metrics.fc import ForgetQuality
from metrics.mia import MembershipInferenceAttack

from loss.unlearning_loss import UnlearningLoss

from data.data_loader import (
    build_retain_loader,
    build_forget_loader,
    build_validation_loader,
)


MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def main():

    # -------------------------
    # Modelo
    # -------------------------

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME
    )

    # -------------------------
    # Estrategia LoRA
    # -------------------------

    strategy = LoRAStrategy()

    model = strategy.prepare_model(model)

    # -------------------------
    # Optimizador
    # -------------------------

    optimizer = OptimizerFactory.adamw(
        parameters=strategy.trainable_parameters(model),
        learning_rate=strategy.learning_rate
    )

    # -------------------------
    # Función de pérdida
    # -------------------------

    loss_function = UnlearningLoss()

    # -------------------------
    # Trainer
    # -------------------------

    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        loss_function=loss_function
    )

    # -------------------------
    # Validator
    # -------------------------

    validator = Validator(
        fsr_metric=ForgetSuccessRate(),
        mu_metric=ModelUtility(),
        fc_metric=ForgetQuality(),
        mia_metric=MembershipInferenceAttack()
    )

    # -------------------------
    # Checkpoint Manager
    # -------------------------

    checkpoint_manager = CheckpointManager(
        output_dir="checkpoints"
    )

    # -------------------------
    # Logger
    # -------------------------

    logger = ExperimentLogger(
        output_dir="logs",
        experiment_name="tinyllama_lora"
    )

    # -------------------------
    # DataLoaders
    # -------------------------

    retain_loader = build_retain_loader()

    forget_loader = build_forget_loader()

    validation_loader = build_validation_loader()

    # -------------------------
    # Trainer Agent
    # -------------------------

    trainer_agent = TrainerAgent(
        trainer=trainer,
        validator=validator,
        checkpoint_manager=checkpoint_manager,
        logger=logger,
        strategy=strategy
    )

    # -------------------------
    # Entrenamiento
    # -------------------------

    trainer_agent.train(
        epochs=5,
        retain_loader=retain_loader,
        forget_loader=forget_loader,
        validation_loader=validation_loader
    )


if __name__ == "__main__":
    main()
