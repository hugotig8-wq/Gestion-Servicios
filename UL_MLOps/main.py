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

from config.config import Config
from config.experiment import Experiment

from loss.unlearning_loss import UnlearningLoss


def compute_reference_loss(model, dataloader, device):
    model.eval()
    total_loss = 0.0
    total_samples = 0
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch.get("attention_mask")
            if attention_mask is not None:
                attention_mask = attention_mask.to(device)
            labels = batch["labels"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            bs = input_ids.size(0)
            total_loss += loss.item() * bs
            total_samples += bs
    if total_samples == 0:
        raise ValueError("El dataloader contiene 0 muestras al calcular reference_loss.")
    return total_loss / total_samples


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

        max_length=experiment.config.max_length,
        
        model_name=experiment.config.model_revision

    )

    reference_model = AutoModelForCausalLM.from_pretrained(

        experiment.config.model_revision

    )

    reference_model.to(device)

    model = AutoModelForCausalLM.from_pretrained(

        experiment.config.model_revision

    )

    model.to(device)

    strategy = LoRAStrategy()

    model = strategy.prepare_model(model)

    optimizer = OptimizerFactory.adamw(

        parameters=strategy.trainable_parameters(model),

        learning_rate=experiment.config.learning_rate

    )

    trainer = Trainer(

        model=model,

        optimizer=optimizer,

        loss_function=UnlearningLoss()

    )

    fsr = ForgetSuccessRate(

            delta_threshold=experiment.config.delta_threshold

    )

    fsr.build_reference(

        reference_model=reference_model,

        dataloader=forget_loader,

        device=device,

        experiment_id=experiment.experiment_id,

        model_revision=experiment.config.model_revision,

        dataset_revision=experiment.config.dataset_revision

    )

    # en main.py, después de reference_model.to(device) y después de fsr.build_reference(...) si quieres:
    reference_loss = compute_reference_loss(reference_model, validation_loader, device)

    # defensa por si sale 0 o negativo (evita ValueError)
    if reference_loss <= 0.0:
        reference_loss = 1e-8

    mu = ModelUtility(reference_loss=reference_loss)

    fc = ForgetQuality(tokenizer)

    mia = MembershipInferenceAttack()
    

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
