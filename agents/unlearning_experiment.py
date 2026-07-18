import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import os
from losses import CombinedUnlearningLoss, RegularizedUnlearningLoss
from config import UnlearningConfig
from metrics import UnlearningMetrics

# ✅ AUTENTICACIÓN
token = os.getenv("HF_TOKEN")
if token:
    login(token=token)
    print("✅ Autenticado en Hugging Face")
else:
    print("⚠️  HF_TOKEN no encontrado. Intentando con credenciales guardadas...")

class UnlearningExperiment:
    def __init__(self, config: UnlearningConfig):
        self.config = config
        self.model_name = "HuggingFaceTB/SmolLM3-3B"
        
        print(f"Descargando modelo: {self.model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True  # ← Importante
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True,
                trust_remote_code=True  # ← Importante
            )
            print("✅ Modelo descargado exitosamente")
        except Exception as e:
            print(f"❌ Error: {e}")
            raise
    
    def train_unlearning(self, retain_dataset, forget_dataset, output_dir="./unlearning_output"):
        """
        Entrenar modelo con Machine Unlearning
        
        Cao & Yang (2015), Cap. 5 - Algorithm 1
        """
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=self.config.learning_rate,
            num_train_epochs=self.config.num_unlearning_epochs,
            per_device_train_batch_size=self.config.retain_batch_size,
            warmup_steps=self.config.warmup_steps,
            weight_decay=self.config.weight_decay,
            fp16=True,
            logging_steps=100,
            save_steps=500,
            eval_strategy="steps",
            eval_steps=self.config.validation_interval,
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=retain_dataset,
            eval_dataset=forget_dataset,
        )
        
        print("Iniciando entrenamiento de unlearning...")
        trainer.train()
        
        return trainer
    
    def validate_unlearning(self, forget_loader, retain_loader):
        """
        Validar que el unlearning funcionó correctamente
        
        Cao & Yang (2015), Cap. 6
        """
        
        print("\n" + "="*60)
        print("VALIDACIÓN DE MACHINE UNLEARNING")
        print("="*60)
        
        # Forget Success Rate
        fsr = UnlearningMetrics.forget_success_rate(
            self.model, forget_loader, 
            AutoModelForCausalLM.from_pretrained(self.model_name)
        )
        print(f"✓ Forget Success Rate (FSR): {fsr:.4f} (objetivo: > 0.9)")
        
        # Model Utility
        mu = UnlearningMetrics.model_utility(self.model, retain_loader)
        print(f"✓ Model Utility (MU): {mu:.4f} (objetivo: > 0.95)")
        
        # Forgetting Consistency
        fc = UnlearningMetrics.forgetting_consistency(self.model, self.original_params)
        print(f"✓ Forgetting Consistency (FC): {fc:.4f} (objetivo: < 0.1)")
        
        print("="*60)
        
        return {
            "fsr": fsr,
            "model_utility": mu,
            "forgetting_consistency": fc
        }


if __name__ == "__main__":
    config = UnlearningConfig()
    experiment = UnlearningExperiment(config)
    print("✅ Experimento inicializado")
