from dataclasses import dataclass

import torch


@dataclass
class MIAResult:

    total_samples: int

    vulnerable_samples: int

    mia: float


class MembershipInferenceAttack:

    def __init__(

        self,

        threshold: float = 0.5

    ):

        self.threshold = threshold

    def compute(

        self,

        model,

        dataloader,

        device: str = "cpu"

    ) -> MIAResult:

        model.eval()

        vulnerable_samples = 0

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

                losses = self._per_sample_loss(

                    outputs.logits,

                    labels

                )

                vulnerable_samples += (

                    losses < self.threshold

                ).sum().item()

                total_samples += losses.numel()

        if total_samples == 0:

            raise ValueError(

                "The dataloader contains no samples."

            )

        mia = (

            vulnerable_samples

            /

            total_samples

        )

        return MIAResult(

            total_samples=total_samples,

            vulnerable_samples=vulnerable_samples,

            mia=mia

        )

    def _per_sample_loss(

        self,

        logits: torch.Tensor,

        labels: torch.Tensor

    ) -> torch.Tensor:

        shift_logits = logits[:, :-1, :].contiguous()

        shift_labels = labels[:, 1:].contiguous()

        batch_size = shift_logits.size(0)

        losses = []

        for index in range(batch_size):

            sample_logits = shift_logits[index]

            sample_labels = shift_labels[index]

            loss = torch.nn.functional.cross_entropy(

                sample_logits,

                sample_labels,

                ignore_index=-100,

                reduction="mean"

            )

            losses.append(loss)

        return torch.stack(losses)
