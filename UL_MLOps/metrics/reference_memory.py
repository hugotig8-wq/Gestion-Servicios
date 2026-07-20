import torch
from datetime import datetime


class ReferenceMemory:

    def __init__(self):

        self.losses = {}

    def store(

        self,

        example_id: str,

        loss: float,

        model_revision: str,

        dataset_revision: str,

        epoch: int = 0

    ):

        self.losses[example_id] = {

            "loss": loss,

            "model_revision": model_revision,

            "dataset_revision": dataset_revision,

            "epoch": epoch,

            "timestamp": datetime.utcnow().isoformat()

        }
    def load(

        self,

        example_id: str

    ):

        return self.losses[example_id]
        
    def exists(

        self,

        example_id: str

    ) -> bool:

        return example_id in self.losses

    def clear(self):

        self.losses.clear()

    def save(

        self,

        path: str

    ):

        torch.save(

            self.losses,

            path

        )

    def load_from_disk(

        self,

        path: str

    ):

        self.losses = torch.load(path)

    def __len__(self):

        return len(self.losses)
