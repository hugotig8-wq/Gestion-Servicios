import torch

from metrics.base_metric import BaseMetric


class ForgetSuccessRate(BaseMetric):

    def compute(

        self,

        model,

        dataloader,

        device

    ) -> float:

        model.eval()

        total_examples = 0

        forgotten_examples = 0

        with torch.no_grad():

            for batch in dataloader:

                input_ids = batch["input_ids"].to(device)

                attention_mask = batch["attention_mask"].to(device)

                labels = batch["labels"].to(device)

                outputs = model(

                    input_ids=input_ids,

                    attention_mask=attention_mask

                )

                predictions = outputs.logits.argmax(dim=-1)

                correct = (

                    predictions == labels

                ).all(dim=1)

                forgotten_examples += (~correct).sum().item()

                total_examples += input_ids.size(0)

        if total_examples == 0:

            return 0.0

        return forgotten_examples / total_examples
