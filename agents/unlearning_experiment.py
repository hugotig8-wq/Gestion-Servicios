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
    """
    Script principal para experimentos de Machine Unlearning
    Cao & Yang (2015)
    """
    
    def __init__(self, config: UnlearningConfig):
        self.config = config
        self.model_name = "HuggingFaceTB/SmolLM3-3B"
        
        print(f"Descargando modelo: {self.model_name}...")
        try:
            # ✅ CORRECCIÓN: Sin load_in_8bit, con dtype en lugar de torch_dtype
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                dtype=torch.float16,  # ← Cambio: torch_dtype → dtype
                device_map="auto",
                trust_remote_code=True
                # ✅ Removido: load_in_8bit=True (no soportado en este modelo)
            )
            print("✅ Modelo descargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            print("\n🔧 Intentando con configuración alternativa...")
            
            # Fallback: Cargar sin optimizaciones
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                print("✅ Modelo cargado (modo CPU/standard)")
            except Exception as e2:
                print(f"❌ Error: {e2}")
                raise
        
        # Guardar parámetros originales (para regularización)
        self.original_params = [p.clone().detach() for p in self.model.parameters()]
        
        # Inicializar losses
        self.combined_loss = CombinedUnlearningLoss(
            alpha=config.alpha,
            beta=config.beta
        )
        
        self.regularized_loss = RegularizedUnlearningLoss(
            alpha=config.alpha,
            beta=config.beta,
            gamma=config.gamma
        )
        self.regularized_loss.set_original_params(self.model)
    
    def train_unlearning(self, retain_dataset, forget_dataset, output_dir="./unlearning_output"):
        """
        Entrenar modelo con Machine Unlearning
        
        Cao & Yang (2015), Cap. 5 - Algorithm 1
        """
        from transformers import Trainer, TrainingArguments
        
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
    
    try:
        experiment = UnlearningExperiment(config)
        print("✅ Experimento inicializado correctamente")
        
        # Prueba simple: generar texto
        print("\n🧪 Prueba de generación de texto:")
        inputs = experiment.tokenizer(
            "Machine unlearning is",
            return_tensors="pt"
        )
        
        with torch.no_grad():
            outputs = experiment.model.generate(
                inputs["input_ids"],
                max_length=50,
                num_return_sequences=1
            )
        
        generated_text = experiment.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Generado: {generated_text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
