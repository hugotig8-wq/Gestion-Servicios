import torch
import torch.nn.functional as F

from metrics.base_metric import BaseMetric


class ForgetSuccessRate(BaseMetric):

    def __init__(

        self,

        delta_threshold: float = 1.0

    ):

        self.delta_threshold = delta_threshold

    def _example_loss(

        self,

        model,

        input_ids,

        attention_mask,

        labels

    ):

        outputs = model(

            input_ids=input_ids,

            attention_mask=attention_mask

        )

        logits = outputs.logits

        return F.cross_entropy(

            logits.view(

                -1,

                logits.size(-1)

            ),

            labels.view(-1),

            ignore_index=-100

        )

    def compute(

        self,

        reference_model,

        unlearned_model,

        dataloader,

        device

    ) -> float:

        reference_model.eval()

        unlearned_model.eval()

        forgotten_examples = 0

        total_examples = 0

        with torch.no_grad():

            for batch in dataloader:

                input_ids = batch["input_ids"].to(device)

                attention_mask = batch["attention_mask"].to(device)

                labels = batch["labels"].to(device)

                batch_size = input_ids.size(0)

                for i in range(batch_size):

                    reference_loss = self._example_loss(

                        reference_model,

                        input_ids[i].unsqueeze(0),

                        attention_mask[i].unsqueeze(0),

                        labels[i].unsqueeze(0)

                    )

                    unlearned_loss = self._example_loss(

                        unlearned_model,

                        input_ids[i].unsqueeze(0),

                        attention_mask[i].unsqueeze(0),

                        labels[i].unsqueeze(0)

                    )

                    delta = (

                        unlearned_loss

                        -

                        reference_loss

                    ).item()

                    if delta >= self.delta_threshold:

                        forgotten_examples += 1

                    total_examples += 1

        if total_examples == 0:

            return 0.0

        return forgotten_examples / total_examples
