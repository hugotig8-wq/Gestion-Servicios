# test_model_simple.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("Descargando tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
print("✅ Tokenizer OK")

print("Descargando modelo...")
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
print("✅ Modelo OK")

print("\nPrueba de generación:")
inputs = tokenizer("Hello", return_tensors="pt")
outputs = model.generate(inputs["input_ids"], max_length=30)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
print("✅ ÉXITO")
