#Luego se puede implementar GA, NPO, SCRUB, KL regularization y selective forgetting.  
import torch
import torch.nn.functional as F

from loss.base_loss import BaseLoss


class UnlearningLoss(BaseLoss):

    def __init__(
        self,
        alpha: float = 1.0,
        beta: float = 1.0
    ):

        self.alpha = alpha
        self.beta = beta

    def compute(

        self,

        retain_outputs,
        forget_outputs,

        retain_labels,
        forget_labels

    ):

        retain_loss = F.cross_entropy(

            retain_outputs.view(
                -1,
                retain_outputs.size(-1)
            ),

            retain_labels.view(-1)

        )

        forget_loss = -F.cross_entropy(

            forget_outputs.view(
                -1,
                forget_outputs.size(-1)
            ),

            forget_labels.view(-1)

        )

        total_loss = (

            self.alpha * retain_loss

            +

            self.beta * forget_loss

        )

        return (

            total_loss,

            retain_loss,

            forget_loss

        )
