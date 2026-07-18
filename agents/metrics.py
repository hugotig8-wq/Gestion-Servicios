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
    def _unpack_batch(batch, device: str = "cpu"):
        """
        Desempaqueta un batch correctamente
        Maneja tanto tuplas como diccionarios
        """
        try:
            if isinstance(batch, dict):
                input_ids = batch['input_ids'].to(device)
                labels = batch.get('labels', input_ids).to(device)
                return input_ids, labels
            
            elif isinstance(batch, (list, tuple)):
                if len(batch) == 3:
                    # (input_ids, attention_mask, labels)
                    input_ids = batch[0].to(device)
                    labels = batch[2].to(device)
                    return input_ids, labels
                elif len(batch) == 2:
                    # (input_ids, labels)
                    input_ids = batch[0].to(device)
                    labels = batch[1].to(device)
                    return input_ids, labels
                else:
                    # Solo input_ids
                    input_ids = batch[0].to(device)
                    return input_ids, input_ids
            
            else:
                # Caso desconocido
                return batch.to(device), batch.to(device)
        
        except Exception as e:
            print(f"Error desempaquetando batch: {e}")
            print(f"Tipo: {type(batch)}")
            if isinstance(batch, (list, tuple)):
                print(f"Longitud: {len(batch)}")
            raise
    
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
        """
        print("      [FSR] Iniciando...")
    
        model.eval()
        correct = 0
        total = 0
        batch_count = 0
    
        with torch.no_grad():
            for batch_idx, batch in enumerate(forget_loader):
                try:
                    print(f"      [FSR] Procesando batch {batch_idx}...")
                
                    # Desempaquetar batch
                    input_ids, labels = UnlearningMetrics._unpack_batch(batch, device)
                    print(f"      [FSR] Input shape: {input_ids.shape}, Labels shape: {labels.shape}")
                
                    # Forward pass
                    print(f"      [FSR] Forward pass...")
                    outputs_unlearn = model(input_ids, labels=labels)
                    print(f"      [FSR] Outputs: {type(outputs_unlearn)}")
                
                    # Extraer loss
                    print(f"      [FSR] Extrayendo loss...")
                    if hasattr(outputs_unlearn, 'loss'):
                        loss_unlearn = outputs_unlearn.loss
                        print(f"      [FSR] Loss (via .loss): {loss_unlearn}")
                    else:
                        loss_unlearn = outputs_unlearn[0]
                        print(f"      [FSR] Loss (via [0]): {loss_unlearn}")
                
                    # Comparar con umbral
                    print(f"      [FSR] Comparando con umbral...")
                    threshold = 2.0
                    correct += (loss_unlearn > threshold).sum().item()
                    total += len(input_ids)
                    batch_count += 1
                
                    print(f"      [FSR] ✅ Batch {batch_idx} OK - correct: {correct}, total: {total}")
                
                except Exception as e:
                    print(f"      [FSR] ❌ Error en batch {batch_idx}: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
    
        print(f"      [FSR] Batches procesados: {batch_count}, Total: {total}, Correct: {correct}")
    
        fsr = correct / total if total > 0 else 0.0
        print(f"      [FSR] FSR = {fsr:.4f}")
    
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
            for batch_idx, batch in enumerate(retain_loader):
                try:
                    # Desempaquetar batch
                    input_ids, labels = UnlearningMetrics._unpack_batch(batch, device)
                    
                    # Forward pass
                    outputs = model(input_ids)
                    
                    # Extraer logits
                    if hasattr(outputs, 'logits'):
                        logits = outputs.logits
                    else:
                        logits = outputs[0]
                    
                    # Calcular predicciones
                    if len(logits.shape) == 2:  # [batch, num_classes]
                        predictions = torch.argmax(logits, dim=-1)
                    else:  # [batch, seq_len, vocab_size]
                        predictions = torch.argmax(logits, dim=-1)
                    
                    # Contar correctas
                    correct += (predictions == labels).sum().item()
                    total += len(input_ids)
                    
                except Exception as e:
                    print(f"⚠️  Error en batch {batch_idx}: {e}")
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
        
        Mide: Cambio mínimo en pesos del modelo
        Objetivo: FC < 0.1 (menos de 10% de cambio)
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
        
        Mide: Capacidad de inferir si un dato fue usado para entrenar
        Objetivo: MIA ≈ 0.5 (sin información)
        """
        model.eval()
        
        member_losses = []
        non_member_losses = []
        
        with torch.no_grad():
            # Pérdidas de miembros
            for batch_idx, batch in enumerate(member_loader):
                try:
                    input_ids, labels = UnlearningMetrics._unpack_batch(batch, device)
                    
                    outputs = model(input_ids, labels=labels)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    member_losses.append(loss.item())
                    
                except Exception as e:
                    print(f"⚠️  Error en member batch {batch_idx}: {e}")
                    continue
            
            # Pérdidas de no-miembros
            for batch_idx, batch in enumerate(non_member_loader):
                try:
                    input_ids, labels = UnlearningMetrics._unpack_batch(batch, device)
                    
                    outputs = model(input_ids, labels=labels)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                    non_member_losses.append(loss.item())
                    
                except Exception as e:
                    print(f"⚠️  Error en non-member batch {batch_idx}: {e}")
                    continue
        
        # Calcular MIA
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
            status = "✅ PASS" if fsr > 0.9 else "⚠️  LOW" if fsr > 0.5 else "❌ FAIL"
            print(f"\n1️⃣  Forget Success Rate (FSR): {fsr:.4f} {status}")
            print(f"   Ecuación: Cao & Yang (2015), Eq. (12)")
            print(f"   Objetivo: > 0.9 (modelo olvida > 90%)")
        
        if "model_utility" in metrics_dict:
            mu = metrics_dict["model_utility"]
            status = "✅ PASS" if mu > 0.95 else "⚠️  LOW" if mu > 0.90 else "❌ FAIL"
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
