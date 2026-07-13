from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "HuggingFaceTB/SmolLM3-3B"  # Nombre exacto del modelo

print("Descargando tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("Descargando modelo...")
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    load_in_8bit=True  # Importante para ahorrar memoria en Codespaces
)

print("✅ Modelo descargado exitosamente!")
print(f"Modelo guardado en: ~/.cache/huggingface/hub/")
