import torch
import torch.nn as nn

class RetainLoss(nn.Module):
    """
    Cao & Yang (2015), Sec. 4.2, Eq. (5)
    L_r = -1/|D_r| * Σ log P(y_i | x_i, θ)
    
    Mantiene precisión en datos a retener
    """
    def __init__(self):
        super().__init__()
        self.cross_entropy = nn.CrossEntropyLoss()
    
    def forward(self, logits, labels):
        return self.cross_entropy(logits, labels)


class ForgetLoss(nn.Module):
    """
    Cao & Yang (2015), Sec. 4.2, Eq. (6)
    L_f = 1/|D_f| * Σ log P(y_i | x_i, θ)
    
    Maximiza pérdida en datos a olvidar
    """
    def __init__(self, temperature=1.0):
        super().__init__()
        self.temperature = temperature
    
    def forward(self, logits, labels):
        loss = torch.nn.functional.cross_entropy(
            logits / self.temperature, 
            labels
        )
        return -loss  # Negativa para maximizar


class CombinedUnlearningLoss(nn.Module):
    """
    Cao & Yang (2015), Sec. 4.3, Eq. (7)
    L_unlearn = α * L_r + β * L_f
    """
    def __init__(self, alpha=1.0, beta=1.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.retain_loss = RetainLoss()
        self.forget_loss = ForgetLoss()
    
    def forward(self, retain_logits, retain_labels, forget_logits, forget_labels):
        l_retain = self.retain_loss(retain_logits, retain_labels)
        l_forget = self.forget_loss(forget_logits, forget_labels)
        return self.alpha * l_retain + self.beta * l_forget


class RegularizedUnlearningLoss(nn.Module):
    """
    Cao & Yang (2015), Sec. 4.4, Eq. (8)
    L_reg = L_unlearn + γ * ||θ - θ_0||²
    
    Evita drift excesivo del modelo original
    """
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.1):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.combined_loss = CombinedUnlearningLoss(alpha, beta)
        self.original_params = None
    
    def set_original_params(self, model):
        self.original_params = [p.clone().detach() for p in model.parameters()]
    
    def forward(self, model, retain_logits, retain_labels, forget_logits, forget_labels):
        combined = self.combined_loss(
            retain_logits, retain_labels,
            forget_logits, forget_labels
        )
        
        if self.original_params is not None:
            reg_loss = sum(
                (p - p0).pow(2).sum()
                for p, p0 in zip(model.parameters(), self.original_params)
            )
            return combined + self.gamma * reg_loss
        
        return combined
