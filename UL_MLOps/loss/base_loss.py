from abc import ABC, abstractmethod

import torch


class BaseLoss(ABC):

    @abstractmethod
    def compute(
        self,
        retain_outputs,
        forget_outputs,
        retain_labels,
        forget_labels
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Devuelve:
            total_loss,
            retain_loss,
            forget_loss
        """
        pass
