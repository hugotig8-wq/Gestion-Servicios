import torch
import torch.nn as nn
from typing import Tuple, Dict

class RetainLoss(nn.Module):
    """
    Retain Loss de Cao & Yang (2015), Sec. 4.2, Eq. (5)
    
    L_r = -1/|D_r| * Σ log P(y_i | x_i, θ)
    
    Propósito: Mantiene precisión en datos a retener
    El modelo debe mantener baja pérdida en estos datos
    """
    
    def __init__(self):
        super().__init__()
        self.cross_entropy = nn.CrossEntropyLoss()
    
    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: Salida del modelo [batch_size, seq_len, vocab_size]
            labels: Labels verdaderos [batch_size, seq_len]
        
        Returns:
            loss: Escalar de pérdida
        """
        # Reshape para cross entropy
        batch_size, seq_len, vocab_size = logits.shape
        logits_flat = logits.reshape(-1, vocab_size)
        labels_flat = labels.reshape(-1)
        
        return self.cross_entropy(logits_flat, labels_flat)


class ForgetLoss(nn.Module):
    """
    Forget Loss de Cao & Yang (2015), Sec. 4.2, Eq. (6)
    
    L_f = 1/|D_f| * Σ log P(y_i | x_i, θ)
    
    Propósito: Maximiza pérdida en datos a olvidar
    Queremos que el modelo tenga ALTA pérdida en estos datos (olvide)
    """
    
    def __init__(self, temperature: float = 1.0):
        super().__init__()
        self.temperature = temperature
        self.cross_entropy = nn.CrossEntropyLoss()
    
    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: Salida del modelo
            labels: Labels a olvidar
        
        Returns:
            loss: Pérdida negativa (maximizamos confusión)
        """
        batch_size, seq_len, vocab_size = logits.shape
        logits_flat = logits.reshape(-1, vocab_size)
        labels_flat = labels.reshape(-1)
        
        # Cross entropy estándar
        ce_loss = self.cross_entropy(logits_flat / self.temperature, labels_flat)
        
        # Retornamos negativa para maximizar (gradient descent lo minimiza)
        return -ce_loss


class CombinedUnlearningLoss(nn.Module):
    """
    Combined Loss de Cao & Yang (2015), Sec. 4.3, Eq. (7)
    
    L_unlearn = α * L_r + β * L_f
    
    Combina ambos objetivos:
    - Minimizar pérdida en datos a retener
    - Maximizar pérdida en datos a olvidar
    
    Referencia: Cao & Yang (2015), Machine Unlearning
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.retain_loss = RetainLoss()
        self.forget_loss = ForgetLoss()
    
    def forward(self, 
                retain_logits: torch.Tensor, 
                retain_labels: torch.Tensor,
                forget_logits: torch.Tensor,
                forget_labels: torch.Tensor) -> Tuple[torch.Tensor, Dict]:
        """
        Args:
            retain_logits: Salida para datos a retener
            retain_labels: Labels para retener
            forget_logits: Salida para datos a olvidar
            forget_labels: Labels para olvidar
        
        Returns:
            loss: Pérdida combinada
            metrics: Dict con componentes de loss
        """
        l_retain = self.retain_loss(retain_logits, retain_labels)
        l_forget = self.forget_loss(forget_logits, forget_labels)
        
        loss = self.alpha * l_retain + self.beta * l_forget
        
        metrics = {
            "retain_loss": l_retain.item(),
            "forget_loss": l_forget.item(),
            "combined_loss": loss.item()
        }
        
        return loss, metrics


class RegularizedUnlearningLoss(nn.Module):
    """
    Regularized Loss de Cao & Yang (2015), Sec. 4.4, Eq. (8)
    
    L_reg = L_unlearn + γ * ||θ - θ_0||²
    
    Evita drift excesivo del modelo original
    Regularización L2 para mantener pesos cercanos a originales
    
    Referencia: Cao & Yang (2015), Machine Unlearning
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0, gamma: float = 0.1):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.combined_loss = CombinedUnlearningLoss(alpha, beta)
        self.original_params = None
    
    def set_original_params(self, model):
        """Guarda parámetros originales para regularización"""
        self.original_params = [p.clone().detach() for p in model.parameters()]
    
    def forward(self, 
                model: nn.Module,
                retain_logits: torch.Tensor, 
                retain_labels: torch.Tensor,
                forget_logits: torch.Tensor,
                forget_labels: torch.Tensor) -> Tuple[torch.Tensor, Dict]:
        """
        Args:
            model: Modelo PyTorch
            retain_logits: Salida para datos a retener
            retain_labels: Labels para retener
            forget_logits: Salida para datos a olvidar
            forget_labels: Labels para olvidar
        
        Returns:
            loss: Pérdida regularizada
            metrics: Dict con detalles
        """
        combined, metrics = self.combined_loss(
            retain_logits, retain_labels,
            forget_logits, forget_labels
        )
        
        # Regularización L2
        if self.original_params is not None:
            reg_loss = sum(
                (p - p0).pow(2).sum()
                for p, p0 in zip(model.parameters(), self.original_params)
            ) / len(self.original_params)
            
            loss = combined + self.gamma * reg_loss
            metrics["regularization_loss"] = reg_loss.item()
        else:
            loss = combined
            reg_loss = torch.tensor(0.0)
        
        metrics["total_loss"] = loss.item()
        
        return loss, metrics
