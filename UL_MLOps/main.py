import uuid
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM

from adaptation.lora_adapter import LoRAStrategy
from adaptation.parameter_strategy import ParameterStrategy

from adaptation.optimizer_factory import OptimizerFactory
from engine.trainer import Trainer
from engine.validator import Validator

from checkpoint.checkpoint_manager import CheckpointManager

from logExp.experiment_logger import ExperimentLogger

from metrics.fsr import ForgetSuccessRate
from metrics.mu import ModelUtility
from metrics.fc import ForgetQuality
from metrics.mia import MembershipInferenceAttack

from agent.trainer_agent import TrainerAgent

from data.data_loader import build_data_loaders


def main():

    config = Config()

    experiment = Experiment(config)

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

        batch_size=experiment.config.batch_size,

        max_length=experiment.config.max_length

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

        learning_rate=experiment.config.learning_rate

    )

    trainer = Trainer(

        optimizer=optimizer

    )

    fsr = ForgetSuccessRate(

            delta_threshold=experiment.config.delta_threshold

    )

    mu = ModelUtility()

    fc = ForgetQuality()

    mia = MembershipInferenceAttack()

    fsr.build_reference(

        reference_model=reference_model,

        dataloader=forget_loader,

        device=device,

        experiment_id=experiment.experiment_id,

        model_revision=experiment.config.model_revision,

        dataset_revision=experiment.config.dataset_revision

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

        experiment = experiment,

        strategy=strategy,

        model=model,

        retain_loader=retain_loader,

        forget_loader=forget_loader,

        validation_loader=validation_loader,

        device=device

    )


if __name__ == "__main__":

    main()
