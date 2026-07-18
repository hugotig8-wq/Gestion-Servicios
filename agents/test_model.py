# test_model.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from huggingface_hub import login

# Login
token = os.getenv("HF_TOKEN")
if token:
    login(token=token)

print("="*60)
print("TEST DE CARGA DE MODELO")
print("="*60)

model_name = "HuggingFaceTB/SmolLM3-3B"

print(f"\n1️⃣  Descargando tokenizer: {model_name}")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print("   ✅ Tokenizer OK")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print(f"\n2️⃣  Descargando modelo...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.float16,  # ← Correcto
        device_map="auto",
        trust_remote_code=True
    )
    print("   ✅ Modelo OK")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("\n   Intentando sin dtype...")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True
        )
        print("   ✅ Modelo OK (sin dtype)")
    except Exception as e2:
        print(f"   ❌ Error: {e2}")
        exit(1)

print(f"\n3️⃣  Información del modelo:")
print(f"   Tipo: {type(model)}")
print(f"   Parámetros: {sum(p.numel() for p in model.parameters()):,}")

print(f"\n4️⃣  Prueba de generación:")
inputs = tokenizer("Hello", return_tensors="pt")
print(f"   Input tokens: {inputs['input_ids']}")

with torch.no_grad():
    outputs = model.generate(inputs["input_ids"], max_length=20)

text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"   Generado: '{text}'")

print("\n✅ TODO OK - El modelo funciona correctamente")
