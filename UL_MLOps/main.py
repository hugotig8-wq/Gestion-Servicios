import uuid
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM

from adaptation.lora_adapter import apply_lora
from adaptation.parameter_strategy import LoRAStrategy

from engine.optimizer_factory import OptimizerFactory
from engine.trainer import Trainer
from engine.validator import Validator

from checkpoint.checkpoint_manager import CheckpointManager

from logging.experiment_logger import ExperimentLogger

from metrics.fsr import ForgetSuccessRate
from metrics.mu import ModelUtility
from metrics.fc import ForgetQuality
from metrics.mia import MembershipInferenceAttack

from agent.trainer_agent import TrainerAgent

from data.data_loader import build_data_loaders


def generate_experiment_id() -> str:

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    random_id = uuid.uuid4().hex[:8]

    return f"{timestamp}_{random_id}"


def main():

    experiment_id = generate_experiment_id()

    model_revision = "TinyLlama-1.1B-Chat-v1.0"

    dataset_revision = "forget_v1"

    device = torch.device(

        "cuda"

        if torch.cuda.is_available()

        else "cpu"

    )

    texts = [

        "Primer documento",

        "Segundo documento",

        "Tercer documento",

    ]

    (

        retain_loader,

        forget_loader,

        validation_loader

    ) = build_data_loaders(

        texts=texts,

        batch_size=8,

        max_length=256

    )

    reference_model = AutoModelForCausalLM.from_pretrained(

        model_revision

    )

    reference_model.to(device)

    model = AutoModelForCausalLM.from_pretrained(

        model_revision

    )

    model.to(device)

    strategy = LoRAStrategy()

    model = apply_lora(

        model,

        strategy

    )

    optimizer = OptimizerFactory.create(

        model,

        learning_rate=1e-4

    )

    trainer = Trainer(

        optimizer=optimizer

    )

    fsr = ForgetSuccessRate()

    mu = ModelUtility()

    fc = ForgetQuality()

    mia = MembershipInferenceAttack()

    fsr.build_reference(

        reference_model=reference_model,

        dataloader=forget_loader,

        device=device,

        experiment_id=experiment_id,

        model_revision=model_revision,

        dataset_revision=dataset_revision

    )

    validator = Validator(

        fsr_metric=fsr,

        mu_metric=mu,

        fc_metric=fc,

        mia_metric=mia,

    )

    checkpoint_manager = CheckpointManager()

    logger = ExperimentLogger()

    trainer_agent = TrainerAgent(

        trainer=trainer,

        validator=validator,

        checkpoint_manager=checkpoint_manager,

        logger=logger

    )

    trainer_agent.train(

        strategy=strategy,

        model=model,

        retain_loader=retain_loader,

        forget_loader=forget_loader,

        validation_loader=validation_loader,

        epochs=5,

        device=device

    )


if __name__ == "__main__":

    main()
