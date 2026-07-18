import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from huggingface_hub import login
import gc

# Login
token = os.getenv("HF_TOKEN")
if token:
    login(token=token)

print("="*60)
print("TEST DE CARGA DE MODELO (OPTIMIZADO)")
print("="*60)

model_name = "HuggingFaceTB/SmolLM3-3B"

print(f"\n1️⃣  Descargando tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print("   ✅ Tokenizer OK")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print(f"\n2️⃣  Descargando modelo con optimizaciones...")
try:
    # ✅ OPTIMIZACIONES CLAVE
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="cpu",  # ← Cargar en CPU primero
        torch_dtype=torch.float32,  # ← Float32 en CPU (menos memoria)
        trust_remote_code=True,
        use_cache=True,  # ← Cachear atenciones (importante para generación)
        offload_folder="./offload"  # ← Spillover a disco
    )
    print("   ✅ Modelo OK")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print(f"\n3️⃣  Información del modelo:")
print(f"   Tipo: {type(model)}")
total_params = sum(p.numel() for p in model.parameters())
print(f"   Parámetros: {total_params:,}")
print(f"   Memoria estimada: {total_params * 4 / (1024**3):.2f} GB (float32)")

print(f"\n4️⃣  Memoria disponible:")
print(f"   RAM disponible: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB" if torch.cuda.is_available() else "   GPU no disponible (usando CPU)")

print(f"\n5️⃣  Prueba de generación (CORTA):")
try:
    inputs = tokenizer("Hello world", return_tensors="pt").to("cpu")
    print(f"   Input tokens: {inputs['input_ids'].shape}")
    
    print("   Generando... (esto puede tardar 30-60 segundos en Codespace)")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_length=30,  # ← MÁS CORTO
            num_beams=1,  # ← Sin beam search (usa greedy)
            do_sample=False,  # ← Sin sampling
            temperature=1.0,
            top_p=1.0
        )
    
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"   ✅ Generado: '{text}'")
    
except RuntimeError as e:
    if "out of memory" in str(e).lower():
        print(f"   ❌ SIN MEMORIA: {e}")
        print("\n   💡 Soluciones:")
        print("      1. Usa modelo más pequeño (phi-2, tiny-llama)")
        print("      2. Reduce max_length")
        print("      3. Usa quantización (bitsandbytes)")
    else:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("✅ TEST COMPLETADO")
print("="*60)
