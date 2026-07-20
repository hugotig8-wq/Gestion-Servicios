import torch


class ReferenceMemory:

    def __init__(self):

        self.losses = {}

    def store(

        self,

        example_id: str,

        loss: float

    ):

        self.losses[example_id] = loss

    def load(

        self,

        example_id: str

    ) -> float:

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
