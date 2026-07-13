from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class SmolLMAgent:
    def __init__(self):
        self.model_name = "HuggingFaceTB/SmolLM3-3B"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True
        )
    
    def razonar(self, prompt, max_length=1000):
        """Hace razonamiento con SmolLM3"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

# Instancia global
agent = SmolLMAgent()
