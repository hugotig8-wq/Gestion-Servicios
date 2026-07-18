import torch
import torch.nn.functional as F
from typing import Callable

class UnlearningMetrics:
    """
    Cao & Yang (2015), Cap. 6 - Experimental Validation
    """
    
    @staticmethod
    def forget_success_rate(model, forget_loader, original_model):
        """
        Cao & Yang (2015), Eq. (12)
        FSR = 1/|D_f| * Σ 1[P(y | x, θ_unlearn) < P(y | x, θ)]
        
        Mide: % de muestras olvidadas correctamente
        Objetivo: FSR > 0.9
        """
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in forget_loader:
                inputs = batch['input_ids'].to(model.device)
                labels = batch['labels'].to(model.device)
                
                # Pérdida del modelo unlearned
                outputs_unlearn = model(inputs, labels=labels)
                loss_unlearn = outputs_unlearn.loss
                
                # Pérdida del modelo original
                outputs_original = original_model(inputs, labels=labels)
                loss_original = outputs_original.loss
                
                # Contador: unlearned tiene mayor pérdida que original
                correct += (loss_unlearn > loss_original).sum().item()
                total += len(inputs)
        
        return correct / total if total > 0 else 0.0
    
    @staticmethod
    def model_utility(model, retain_loader):
        """
        Cao & Yang (2015), Sec. 6.3
        MU = Accuracy(D_retain) / Accuracy_original
        
        Mide: Mantención de precisión en datos retenidos
        Objetivo: MU > 0.95
        """
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in retain_loader:
                inputs = batch['input_ids'].to(model.device)
                labels = batch['labels'].to(model.device)
                
                outputs = model(inputs)
                logits = outputs.logits if hasattr(outputs, 'logits') else outputs
                
                predictions = torch.argmax(logits, dim=-1)
                correct += (predictions == labels).sum().item()
                total += len(inputs)
        
        return correct / total if total > 0 else 0.0
    
    @staticmethod
    def forgetting_consistency(model, original_params):
        """
        Cao & Yang (2015), Eq. (14)
        FC = || θ_unlearn - θ_original || / || θ_original ||
        
        Mide: Cambio mínimo en pesos del modelo
        Objetivo: FC < 0.1
        """
        numerator = 0.0
        denominator = 0.0
        
        for p_current, p_original in zip(model.parameters(), original_params):
            numerator += torch.norm(p_current - p_original).item() ** 2
            denominator += torch.norm(p_original).item() ** 2
        
        if denominator == 0:
            return 0.0
        
        return (numerator ** 0.5) / (denominator ** 0.5)
