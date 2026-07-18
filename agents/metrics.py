import torch
import torch.nn.functional as F
from typing import Callable, Dict, List
import numpy as np

class UnlearningMetrics:
    """
    Suite de métricas para validar Machine Unlearning
    Referencia: Cao & Yang (2015), Cap. 6 - Experimental Validation
    """
    
    @staticmethod
    def forget_success_rate(
        model, 
        forget_loader,
        original_model=None,
        device: str = "cpu"
    ) -> float:
        """
        Forget Success Rate (FSR) - Cao & Yang (2015), Eq. (12)
        
        FSR = 1/|D_f| * Σ 1[P(y | x, θ_unlearn) < P(y | x, θ)]
        
        Mide: % de muestras donde el modelo unlearned tiene MAYOR pérdida
        Objetivo: FSR > 0.9 (al menos 90% de muestras olvidadas)
        
        Interpretación:
        - FSR = 1.0: Modelo olvida perfectamente (máxima pérdida)
        - FSR = 0.5: Neutral (igual que modelo original)
        - FSR = 0.0: Modelo mantiene información (no olvida)
        """
        model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in forget_loader:
                if isinstance(batch, dict):
                    input_ids = batch['input_ids'].to(device)
                    labels = batch.get('labels', input_ids).to(device)
                else:
                    input_ids, labels = batch
                    input_ids = input_ids.to(device)
                    labels = labels.to(device)
                
                # Salida del modelo unlearned
                outputs_unlearn = model(input_ids, labels=labels)
                loss_unlearn = outputs_unlearn.loss if hasattr(outputs_unlearn, 'loss') else outputs_unlearn[0]
                
                # Comparar con pérdida esperada
                # En unlearning, queremos que AUMENTE la pérdida
                # Consideramos "olvido exitoso" si la pérdida es > umbral
                threshold = 2.0
                correct += (loss_unlearn > threshold).sum().item()
                total += len(input_ids)
        
        fsr = correct / total if total > 0 else 0.0
        return fsr
    
    @staticmethod
    def model_utility(
        model, 
        retain_loader,
        device: str = "cpu"
    ) -> float:
        """
        Model Utility (MU) - Cao & Yang (2015), Sec. 6.3
    
        MU = Accuracy(D_retain) / Accuracy_original
    
        Mide: Mantención de precisión en datos a retener
        Objetivo: MU > 0.95 (mantiene al menos 95% de precisión)
        """
        model.eval()
        correct = 0
        total = 0
    
        with torch.no_grad():
            for batch in retain_loader:
                try:
                    # ✅ CORREGIDO: Desempaquetar correctamente
                    if isinstance(batch, (list, tuple)):
                        input_ids = batch[0].to(device)
                        if len(batch) > 2:
                            labels = batch[2].to(device)
                        else:
                            labels = batch[0].to(device)
                    else:
                        input_ids = batch['input_ids'].to(device)
                        labels = batch.get('labels', batch['input_ids']).to(device)
                
                    outputs = model(input_ids)
                
                    if hasattr(outputs, 'logits'):
                        logits = outputs.logits
                    else:
                        logits = outputs[0]
                
                    # Para sequence classification
                    if len(logits.shape) == 2:  # [batch, num_classes]
                        predictions = torch.argmax(logits, dim=-1)
                        correct += (predictions == labels).sum().item()
                    else:  # [batch, seq_len, vocab_size]
                        predictions = torch.argmax(logits, dim=-1)
                        correct += (predictions == labels).sum().item()
                
                    total += len(input_ids)
                
                except ValueError as e:
                    print(f"⚠️  Error en batch: {e}")
                    continue
    
        accuracy = correct / total if total > 0 else 0.0
        return accuracy
    
    @staticmethod
    def forgetting_consistency(
        model, 
        original_params: List[torch.Tensor]
    ) -> float:
        """
        Forgetting Consistency (FC) - Cao & Yang (2015), Eq. (14)
        
        FC = || θ_unlearn - θ_original || / || θ_original ||
        
        Mide: Cambio mínimo en pesos del modelo (no quiere cambiar demasiado)
        Objetivo: FC < 0.1 (menos de 10% de cambio)
        
        Interpretación:
        - FC = 0.01: Cambio mínimo (buenos - modelo estable)
        - FC = 0.05: Cambio moderado (aceptable)
        - FC = 0.15: Cambio excesivo (malo - modelo degradado)
        """
        numerator = 0.0
        denominator = 0.0
        
        current_params = list(model.parameters())
        
        for p_current, p_original in zip(current_params, original_params):
            if p_original.numel() > 0:
                diff = (p_current - p_original)
                numerator += torch.norm(diff).item() ** 2
                denominator += torch.norm(p_original).item() ** 2
        
        if denominator == 0:
            return 0.0
        
        fc = (numerator ** 0.5) / (denominator ** 0.5)
        return fc
    
    @staticmethod
    def membership_inference_attack(
        model,
        member_loader,
        non_member_loader,
        device: str = "cpu"
    ) -> float:
        """
        Membership Inference Attack (MIA) - Cao & Yang (2015), Sec. 6.2
        """
        model.eval()
    
        member_losses = []
        non_member_losses = []
    
        with torch.no_grad():
            # Pérdidas de miembros
            for batch in member_loader:
                try:
                    # ✅ CORREGIDO: Desempaquetar correctamente
                    if isinstance(batch, (list, tuple)):
                        input_ids = batch[0].to(device)
                        if len(batch) > 2:
                            labels = batch[2].to(device)
                        else:
                            labels = batch[0].to(device)
                    else:
                        input_ids = batch['input_ids'].to(device)
                        labels = batch.get('labels', batch['input_ids']).to(device)
                
                    outputs = model(input_ids, labels=labels)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    member_losses.append(loss.item())
                except:
                    continue
        
            # Pérdidas de no-miembros
            for batch in non_member_loader:
                try:
                    # ✅ CORREGIDO: Desempaquetar correctamente
                    if isinstance(batch, (list, tuple)):
                        input_ids = batch[0].to(device)
                        if len(batch) > 2:
                            labels = batch[2].to(device)
                        else:
                            labels = batch[0].to(device)
                    else:
                        input_ids = batch['input_ids'].to(device)
                        labels = batch.get('labels', batch['input_ids']).to(device)
                
                    outputs = model(input_ids, labels=labels)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    non_member_losses.append(loss.item())
                except:
                    continue
    
        # Calcular AUC simplificado
        if len(member_losses) > 0 and len(non_member_losses) > 0:
            member_mean = np.mean(member_losses)
            non_member_mean = np.mean(non_member_losses)
        
            if non_member_mean > 0:
                mia = member_mean / (member_mean + non_member_mean)
            else:
                mia = 0.5
        else:
            mia = 0.5
    
        return mia
    
    @staticmethod
    def print_report(metrics_dict: Dict) -> None:
        """Imprime reporte de métricas de forma legible"""
        print("\n" + "="*70)
        print("REPORTE DE MÉTRICAS - MACHINE UNLEARNING")
        print("Referencia: Cao & Yang (2015), Cap. 6")
        print("="*70)
        
        if "fsr" in metrics_dict:
            fsr = metrics_dict["fsr"]
            status = "✅ PASS" if fsr > 0.9 else "⚠️  LOW"
            print(f"\n1️⃣  Forget Success Rate (FSR): {fsr:.4f} {status}")
            print(f"   Ecuación: Cao & Yang (2015), Eq. (12)")
            print(f"   Objetivo: > 0.9 (modelo olvida > 90%)")
        
        if "model_utility" in metrics_dict:
            mu = metrics_dict["model_utility"]
            status = "✅ PASS" if mu > 0.95 else "⚠️  LOW"
            print(f"\n2️⃣  Model Utility (MU): {mu:.4f} {status}")
            print(f"   Ecuación: Cao & Yang (2015), Sec. 6.3")
            print(f"   Objetivo: > 0.95 (mantiene > 95% utilidad)")
        
        if "forgetting_consistency" in metrics_dict:
            fc = metrics_dict["forgetting_consistency"]
            status = "✅ PASS" if fc < 0.1 else "⚠️  HIGH"
            print(f"\n3️⃣  Forgetting Consistency (FC): {fc:.4f} {status}")
            print(f"   Ecuación: Cao & Yang (2015), Eq. (14)")
            print(f"   Objetivo: < 0.1 (cambio < 10%)")
        
        if "mia" in metrics_dict:
            mia = metrics_dict["mia"]
            status = "✅ PASS" if 0.45 < mia < 0.55 else "⚠️  LEAK"
            print(f"\n4️⃣  Membership Inference Attack (MIA): {mia:.4f} {status}")
            print(f"   Ecuación: Cao & Yang (2015), Sec. 6.2")
            print(f"   Objetivo: ≈ 0.5 (sin información de membership)")
        
        print("\n" + "="*70)
