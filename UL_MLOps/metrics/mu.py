from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass
class MUResult:

    loss_before: float

    loss_after: float

    mu: float


class MU:

    def __init__(

        self,

        reference_loss: float

    ):

        self.reference_loss = reference_loss

    def compute(

        self,

        model,

        dataloader,

        device: str = "cpu"

    ) -> MUResult:

        model.eval()

        total_loss = 0.0

        total_samples = 0

        with torch.no_grad():

            for batch in dataloader:

                input_ids = batch["input_ids"].to(

                    device

                )

                attention_mask = batch.get(

                    "attention_mask"

                )

                if attention_mask is not None:

                    attention_mask = attention_mask.to(

                        device

                    )

                labels = batch["labels"].to(

                    device

                )

                outputs = model(

                    input_ids=input_ids,

                    attention_mask=attention_mask,

                    labels=labels

                )

                loss = outputs.loss

                batch_size = input_ids.size(0)

                total_loss += (

                    loss.item()

                    *

                    batch_size

                )

                total_samples += batch_size

        if total_samples == 0:

            raise ValueError(

                "The dataloader contains no samples."

            )

        loss_after = (

            total_loss

            /

            total_samples

        )

        mu = self._compute_mu(

            loss_after

        )

        return MUResult(

            loss_before=self.reference_loss,

            loss_after=loss_after,

            mu=mu

        )

    def _compute_mu(

        self,

        loss_after: float

    ) -> float:

        if self.reference_loss <= 0:

            raise ValueError(

                "reference_loss must be greater than zero."

            )

        return max(

            0.0,

            1.0

            -

            (

                abs(

                    loss_after

                    -

                    self.reference_loss

                )

                /

                self.reference_loss

            )

              )
