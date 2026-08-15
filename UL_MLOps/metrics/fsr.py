import torch 
import torch.nn.functional as F

from metrics.base_metric import BaseMetric
from metrics.reference_memory import ReferenceMemory   # + import


class ForgetSuccessRate(BaseMetric):

    def __init__(

        self,

        delta_threshold: float = 1.0

    ):

        self.delta_threshold = delta_threshold

        self.reference_memory = ReferenceMemory()

        self.avetage_delta = 0.0

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

        model,

        dataloader,

        device

    ) -> float:

        if len(self.reference_memory) == 0:

            raise RuntimeError(

                "Reference memory is empty."

            )

        model.eval()

        forgotten_examples = 0

        total_examples = 0

        total_delta = 0.0

        with torch.no_grad():

            for batch in dataloader:

                input_ids = batch["input_ids"].to(device)

                attention_mask = batch["attention_mask"].to(device)

                labels = batch["labels"].to(device)

                ids = batch["id"]

                batch_size = input_ids.size(0)

                for i in range(batch_size):

                    current_loss = self._example_loss(

                        model,

                        input_ids[i].unsqueeze(0),

                        attention_mask[i].unsqueeze(0),

                        labels[i].unsqueeze(0)

                    )

                    if isinstance(reference_record, dict):
                        reference_loss = reference_record.get("loss")
                    else:
                        reference_loss = reference_record
                    # asegurar floats
                    current_val = current_loss.item() if torch.is_tensor(current_loss) else float(current_loss)
                    reference_val = reference_loss.item() if torch.is_tensor(reference_loss) else float(reference_loss)
                    delta = current_val - reference_val

                    total_delta += delta

                    if delta >= self.delta_threshold:

                        forgotten_examples += 1

                    total_examples += 1

        self.average_delta = total_delta / total_examples

        return forgotten_examples / total_examples

    def build_reference(

        self,

        experiment_id,

        reference_model,

        dataloader,

        device,

        model_revision,

        dataset_revision

    ):

        reference_model.eval()

        self.reference_memory.clear()

        with torch.no_grad():

            for batch in dataloader:

                input_ids = batch["input_ids"].to(device)

                attention_mask = batch["attention_mask"].to(device)

                labels = batch["labels"].to(device)

                ids = batch["id"]

                batch_size = input_ids.size(0)

                for i in range(batch_size):

                    loss = self._example_loss(

                        reference_model,

                        input_ids[i].unsqueeze(0),

                        attention_mask[i].unsqueeze(0),

                        labels[i].unsqueeze(0)

                    )

                    self.reference_memory.store(

                        example_id=ids[i],

                        experiment_id=experiment_id,

                        loss=loss.item() if torch.is_tensor(loss) else float(loss),
                        
                        model_revision=model_revision,

                        dataset_revision=dataset_revision,

                        epoch=0

                    )
