import torch
from dataclasses import dataclass

from metrics.fsr import ForgetSuccessRate
from metrics.mu import ModelUtility
from metrics.fc import ForgetQuality
from metrics.mia import MembershipInferenceAttack


@dataclass
class ValidationResult:

    fsr: float

    mu: float

    fc: float

    mia: float


class Validator:

    def __init__(

        self,

        fsr_metric: ForgetSuccessRate,

        mu_metric: ModelUtility,

        fc_metric: ForgetQuality,

        mia_metric: MembershipInferenceAttack

    ):

        self.fsr_metric = fsr_metric

        self.mu_metric = mu_metric

        self.fc_metric = fc_metric

        self.mia_metric = mia_metric

    def validate(

        self,

        model,

        retain_loader,

        forget_loader,

        validation_loader,

        device = 'cpu'

    ) -> ValidationResult:
        #model.eval() desactiva también el Dropout (que sirve para evitar overfitting, aleatorias las neuronas que elija para cada batch)..
        model.eval()#Permite que no se haga BatchNorm (aunque TinyLlama usa RMSNorm que no depende del modo de entrenamiento/evaluacion).
        #model.eval() usa todas las neuronas para inferir en ese punto del pipeline.

        with torch.no_grad():#No input-embedding-transformer-linear-loss, sólo el resultado sin grafo.
        #torch.no_grad() Reduce y acelera evaluación, evita el grafo del backward().
            fsr = self.fsr_metric.compute(

                model,

                forget_loader

            )

            mu = self.mu_metric.compute(

                model,

                validation_loader,

                device=device

            )

            fc = self.fc_metric.compute(

                model,

                retain_loader,

                forget_loader

            )

            mia = self.mia_metric.compute(

                model,

                retain_loader,

                forget_loader

            )

        return ValidationResult(

            fsr=fsr,

            mu=mu,

            fc=fc,

            mia=mia

  )
