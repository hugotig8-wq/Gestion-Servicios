import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Carga ligera para CPU sin necesidad de bitsandbytes
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,  # O torch.float16
    device_map="cpu",
    low_cpu_mem_usage=True
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
