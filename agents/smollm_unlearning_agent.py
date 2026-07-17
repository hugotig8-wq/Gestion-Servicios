from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import json
from pathlib import Path
from typing import Dict, List
import re

class SmolLMUnlearningAgent:
    """
    Agente especializado en analizar SmolLM3-3B-Base y generar plans para
    implementar Machine Unlearning de Cao & Yang (2015)
    """
    
    def __init__(self):
        self.model_name = "HuggingFaceTB/SmolLM3-3B"
        print("Cargando modelo SmolLM3...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True
        )
        
        # Referencias del paper Cao & Yang (2015)
        self.cao_yang_references = {
            "capitulo_1": "Introduction - Machine Learning and Unlearning Paradigm",
            "capitulo_2": "Related Work and Theoretical Foundation",
            "capitulo_3": "Machine Unlearning Framework - Core Concepts",
            "capitulo_4": "Loss Function Design and Gradient-based Methods",
            "capitulo_5": "Implementation Details and Algorithms",
            "capitulo_6": "Experimental Validation",
            "capitulo_7": "Applications and Future Work"
        }
    
    def analizar_estructura_smollm(self, repo_path: str) -> Dict:
        """
        Analiza la estructura completa de SmolLM3-3B-Base
        Identifica:
        - Arquitectura de red
        - Funciones de pérdida actuales
        - Callbacks de entrenamiento
        - Layers de atención
        """
        
        print("🔍 Analizando estructura de SmolLM3...")
        
        estructura = {
            "archivos_principales": [],
            "loss_functions": [],
            "attention_mechanisms": [],
            "training_loops": [],
            "architecture_files": []
        }
        
        # Buscar archivos críticos
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    contenido = self._leer_archivo(filepath)
                    
                    # Detectar componentes
                    if 'loss' in file.lower() or 'criterion' in contenido:
                        estructura["loss_functions"].append(filepath)
                    
                    if 'attention' in file.lower() or 'attn' in contenido:
                        estructura["attention_mechanisms"].append(filepath)
                    
                    if 'train' in file.lower() or 'trainer' in contenido:
                        estructura["training_loops"].append(filepath)
                    
                    if 'model' in file.lower() or 'config' in contenido:
                        estructura["architecture_files"].append(filepath)
                    
                    estructura["archivos_principales"].append({
                        "path": filepath,
                        "size": len(contenido),
                        "has_forward": "def forward" in contenido
                    })
        
        return estructura
    
    def generar_plan_unlearning(self, estructura: Dict) -> Dict:
        """
        Genera plan detallado para implementar machine unlearning
        Basado en Cao & Yang (2015)
        """
        
        prompt = f"""
        TAREA: Generar plan completo para implementar Machine Unlearning de Cao & Yang (2015)
        en el modelo SmolLM3 de Hugging Face.
        
        REFERENCIA TEÓRICA:
        Cao & Yang (2015) proponen un framework donde:
        
        CAPÍTULO 3 - Marco Matemático:
        La función de pérdida de unlearning se define como:
        L_unlearn = L_original - λ * ∇L_forget
        
        donde:
        - L_original: pérdida estándar del modelo
        - L_forget: pérdida de los datos a olvidar
        - λ: factor de regularización
        
        CAPÍTULO 4 - Funciones de Pérdida:
        1. Cross-Entropy Loss estándar (mantener)
        2. Forget Loss (nueva): maximiza pérdida en datos a olvidar
        3. Retain Loss (nueva): minimiza pérdida en datos a retener
        4. Balance Loss: combina ambas
        
        L_unlearn = α * L_retain + β * (-L_forget)
        
        Estructura actual de SmolLM3:
        {json.dumps(estructura, indent=2)}
        
        GENERA:
        1. Fases de implementación (ordena por complejidad)
        2. Archivos a modificar (con líneas específicas)
        3. Nuevas clases/funciones a crear
        4. Cambios en training loop
        5. Validación y testing
        
        Para cada cambio, especifica:
        - Línea aproximada del archivo
        - Código actual vs. código propuesto
        - Justificación técnica con referencia al capítulo del paper
        - Impacto en rendimiento
        
        Responde en JSON detallado.
        """
        
        resultado = self._razonar(prompt)
        return self._parsear_json(resultado)
    
    def analizar_loss_functions(self, repo_path: str) -> Dict:
        """
        Analiza las funciones de pérdida actuales
        y propone adaptaciones para Cao & Yang
        """
        
        archivos_loss = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if 'loss' in file.lower() and file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    contenido = self._leer_archivo(filepath)
                    archivos_loss.append({
                        "archivo": filepath,
                        "contenido": contenido[:2000]  # Primeros 2000 chars
                    })
        
        prompt = f"""
        ANALIZAR FUNCIONES DE PÉRDIDA PARA MACHINE UNLEARNING
        
        Archivos de pérdida encontrados:
        {json.dumps(archivos_loss, indent=2, ensure_ascii=False)}
        
        CAPÍTULO 4 DE CAO & YANG (2015):
        Define 4 tipos de funciones de pérdida para unlearning:
        
        1. RETAIN LOSS (L_r):
           L_r = -1/|D_r| * Σ log P(y_i | x_i, θ)
           
           Propósito: Mantener precisión en datos a retener
           Referencia: Cao & Yang (2015), Sec. 4.2, Eq. (5)
        
        2. FORGET LOSS (L_f):
           L_f = 1/|D_f| * Σ log P(y_i | x_i, θ)
           
           Propósito: Maximizar pérdida en datos a olvidar
           Referencia: Cao & Yang (2015), Sec. 4.2, Eq. (6)
        
        3. COMBINED LOSS (L_unlearn):
           L_unlearn = α * L_r + β * L_f
           
           Propósito: Balance entre ambos objetivos
           Referencia: Cao & Yang (2015), Sec. 4.3, Eq. (7)
        
        4. REGULARIZED LOSS (L_reg):
           L_reg = L_unlearn + γ * ||θ - θ_0||²
           
           Propósito: Evitar drift del modelo original
           Referencia: Cao & Yang (2015), Sec. 4.4, Eq. (8)
        
        TAREA:
        1. Identifica la función de pérdida actual
        2. Propone cómo adaptarla a cada tipo
        3. Genera código PyTorch para cada loss
        4. Especifica hiperparámetros (α, β, γ)
        5. Sugiere estrategia de balancing
        
        Responde en JSON con:
        - tipo_loss
        - ecuacion_cao_yang
        - codigo_pytorch
        - referencias
        - parametros
        
        """
        
        resultado = self._razonar(prompt)
        return self._parsear_json(resultado)
    
    def proponer_modificaciones_training(self, repo_path: str) -> Dict:
        """
        Propone modificaciones al training loop
        para integrar machine unlearning
        """
        
        # Buscar trainer/training loop
        training_code = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py') and any(x in file.lower() for x in ['train', 'trainer', 'loop']):
                    filepath = os.path.join(root, file)
                    contenido = self._leer_archivo(filepath)
                    training_code.append({
                        "archivo": filepath,
                        "contenido": contenido[:3000]
                    })
        
        prompt = f"""
        ADAPTACIÓN DEL TRAINING LOOP PARA MACHINE UNLEARNING
        
        Código actual de training:
        {json.dumps(training_code, indent=2, ensure_ascii=False)}
        
        CAPÍTULO 5 DE CAO & YANG (2015):
        Describe el algoritmo de unlearning en el training loop:
        
        ALGORITMO 1: Machine Unlearning Training (Cao & Yang, Sec. 5.1)
        
        ```
        for epoch in epochs:
            for batch in train_data:
                # 1. FORWARD PASS
                outputs = model(batch)
                
                # 2. RETAIN LOSS (datos a mantener)
                L_retain = compute_retain_loss(outputs, batch)
                
                # 3. FORGET LOSS (datos a olvidar)
                L_forget = compute_forget_loss(forget_batch)
                
                # 4. COMBINED LOSS
                L_total = α * L_retain + β * L_forget
                
                # 5. BACKWARD PASS
                L_total.backward()
                
                # 6. GRADIENT CLIPPING (estabilidad)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                # 7. OPTIMIZER STEP
                optimizer.step()
                optimizer.zero_grad()
                
                # 8. LOGGING
                log_unlearning_metrics(L_retain, L_forget, L_total)
        ```
        
        CAPÍTULO 5.2 - Optimizaciones:
        - Batch normalization para datos olvidados
        - Gradient accumulation
        - Mixed precision training
        - Validator de "forgetting success"
        
        TAREA:
        1. Adapta el training loop actual
        2. Integra retain y forget batches
        3. Propone sistema de validation
        4. Sugiere optimizaciones de memoria
        5. Define métricas de éxito del unlearning
        
        Responde con:
        - codigo_adaptado
        - cambios_especificos
        - lineas_aproximadas
        - metricas_nuevo_entrenamiento
        - referencias_cao_yang
        """
        
        resultado = self._razonar(prompt)
        return self._parsear_json(resultado)
    
    def generar_metricas_unlearning(self) -> Dict:
        """
        Propone métricas para validar que el unlearning funcionó
        Basado en Cao & Yang (2015) Capítulo 6
        """
        
        prompt = """
        MÉTRICAS DE VALIDACIÓN PARA MACHINE UNLEARNING
        Referencia: Cao & Yang (2015), Capítulo 6 - Experimental Validation
        
        CAPÍTULO 6.1 - Métricas de Efectividad:
        
        1. FORGET SUCCESS RATE (FSR):
           FSR = 1/|D_f| * Σ 1[P(y | x, θ_unlearn) < P(y | x, θ_original)]
           
           Mide: % de muestras olvidadas correctamente
           Objetivo: FSR > 0.9
           Referencia: Cao & Yang (2015), Eq. (12)
        
        2. MEMBERSHIP INFERENCE ATTACK (MIA):
           MIA = 1 - Accuracy(classifier_pertenencia)
           
           Mide: Dificultad de inferir si dato fue usado para entrenar
           Objetivo: MIA cercano a 50% (sin información)
           Referencia: Cao & Yang (2015), Sec. 6.2
        
        3. MODEL UTILITY (MU):
           MU = Accuracy(D_retain) / Accuracy_original
           
           Mide: Mantención de precisión en datos retenidos
           Objetivo: MU > 0.95
           Referencia: Cao & Yang (2015), Sec. 6.3
        
        4. FORGETTING CONSISTENCY (FC):
           FC = || θ_unlearn - θ_original || / || θ_original ||
           
           Mide: Cambio mínimo en pesos del modelo
           Objetivo: FC < 0.1 (cambio controlado)
           Referencia: Cao & Yang (2015), Eq. (14)
        
        CAPÍTULO 6.4 - Suite de Testing:
        
        1. Test de Generación:
           - Generar texto similar a datos olvidados
           - Verificar que no repita patrones olvidados
           
        2. Test de Confidencialidad:
           - Implementar MIA attack
           - Evaluar si es defenible
           
        3. Test de Estabilidad:
           - Múltiples unlearning rounds
           - Verificar convergencia
           
        4. Test de Performance:
           - Benchmarks en tareas downstream
           - Comparar con modelo original
        
        Genera:
        1. Código PyTorch para cada métrica
        2. Dataset de prueba simulado
        3. Benchmark suite
        4. Reporting dashboard
        5. Thresholds de validación
        
        Responde en JSON con implementaciones.
        """
        
        resultado = self._razonar(prompt)
        return self._parsear_json(resultado)
    
    def generar_codigo_implementacion(self, aspecto: str) -> str:
        """
        Genera código listo para usar
        aspecto: 'loss_functions', 'training_loop', 'validation', 'config'
        """
        
        prompts = {
            "loss_functions": """
            Genera clases PyTorch para las 4 funciones de pérdida de Cao & Yang (2015):
            
            1. RetainLoss (Cao & Yang, Sec. 4.2)
            2. ForgetLoss (Cao & Yang, Sec. 4.2)
            3. CombinedUnlearningLoss (Cao & Yang, Sec. 4.3)
            4. RegularizedUnlearningLoss (Cao & Yang, Sec. 4.4)
            
            Requisitos:
            - Herencia de torch.nn.Module
            - Configuración de hiperparámetros
            - Documentación con referencias al paper
            - Ejemplos de uso
            - Type hints
            
            Responde solo código Python válido.
            """,
            
            "training_loop": """
            Genera un trainer adaptado para machine unlearning:
            
            Características (Cao & Yang, Cap. 5):
            - Manejo de retain y forget batches
            - Cálculo de múltiples losses
            - Logging de métricas de unlearning
            - Validación periódica
            - Checkpointing
            
            Utiliza transformers.Trainer si es posible
            Documenta con referencias a capítulos específicos
            
            Responde solo código Python.
            """,
            
            "validation": """
            Genera suite de validación:
            
            Métricas (Cao & Yang, Cap. 6):
            1. Forget Success Rate
            2. Membership Inference Attack
            3. Model Utility
            4. Forgetting Consistency
            
            Implementa en PyTorch con:
            - Funciones de cálculo
            - Datasets de prueba
            - Reporting
            
            Responde solo código.
            """,
            
            "config": """
            Genera archivo de configuración para unlearning:
            
            Parámetros de Cao & Yang (2015):
            - α, β, γ (coeficientes de loss)
            - Tamaño de forget/retain batches
            - Learning rate
            - Épocas de unlearning
            - Thresholds de validación
            
            Formato: JSON compatible con HuggingFace
            Documenta cada parámetro
            """
        }
        
        prompt = prompts.get(aspecto, "Genera código para machine unlearning")
        resultado = self._razonar(prompt)
        return resultado
    
    def crear_reporte_completo(self, repo_path: str, output_file: str = "plan_unlearning.json") -> Dict:
        """
        Genera reporte completo con plan de implementación
        """
        
        print("📊 Generando reporte completo...")
        
        # Análisis
        print("  1️⃣  Analizando estructura...")
        estructura = self.analizar_estructura_smollm(repo_path)
        
        print("  2️⃣  Generando plan...")
        plan = self.generar_plan_unlearning(estructura)
        
        print("  3️⃣  Analizando loss functions...")
        loss_analysis = self.analizar_loss_functions(repo_path)
        
        print("  4️⃣  Proponiendo training adaptations...")
        training_mods = self.proponer_modificaciones_training(repo_path)
        
        print("  5️⃣  Generando métricas...")
        metricas = self.generar_metricas_unlearning()
        
        # Generar código
        print("  6️⃣  Generando código...")
        codigo_losses = self.generar_codigo_implementacion("loss_functions")
        codigo_trainer = self.generar_codigo_implementacion("training_loop")
        codigo_validation = self.generar_codigo_implementacion("validation")
        codigo_config = self.generar_codigo_implementacion("config")
        
        # Compilar reporte
        reporte = {
            "titulo": "Plan de Implementación: Machine Unlearning en SmolLM3",
            "referencia_teorica": "Cao & Yang (2015) - Machine Unlearning",
            "fecha": str(Path.cwd()),
            
            "seccion_1_analisis": {
                "titulo": "Análisis de Estructura de SmolLM3",
                "contenido": estructura,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 5 - Implementation Details"
            },
            
            "seccion_2_plan": {
                "titulo": "Plan de Implementación Detallado",
                "contenido": plan,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 3-5"
            },
            
            "seccion_3_loss_functions": {
                "titulo": "Análisis y Adaptación de Funciones de Pérdida",
                "contenido": loss_analysis,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 4 - Loss Function Design",
                "codigo": codigo_losses
            },
            
            "seccion_4_training": {
                "titulo": "Adaptación del Training Loop",
                "contenido": training_mods,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 5 - Algorithms",
                "codigo": codigo_trainer
            },
            
            "seccion_5_validation": {
                "titulo": "Métricas y Validación",
                "contenido": metricas,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 6 - Experimental Validation",
                "codigo": codigo_validation
            },
            
            "seccion_6_configuracion": {
                "titulo": "Configuración de Hiperparámetros",
                "codigo": codigo_config,
                "capitulo_referencia": "Cao & Yang (2015), Cap. 6 - Experimental Setup"
            },
            
            "proximos_pasos": [
                {
                    "paso": 1,
                    "nombre": "Setup del entorno",
                    "acciones": [
                        "identificar el modelo SmolLM3-3B-Base completo HuggingFaceTB/SmolLM3-3B-Base",
                        "Instalar dependencias para SmolLm3-3B (no base)",
                        "Crear estructura de directorios"
                    ]
                },
                {
                    "paso": 2,
                    "nombre": "Implementación de Loss Functions",
                    "acciones": [
                        "Crear archivo losses.py",
                        "Implementar 4 tipos de loss",
                        "Crear tests unitarios"
                    ]
                },
                {
                    "paso": 3,
                    "nombre": "Adaptación del Trainer",
                    "acciones": [
                        "Modificar training loop",
                        "Integrar forget/retain batches",
                        "Agregar logging"
                    ]
                },
                {
                    "paso": 4,
                    "nombre": "Validación",
                    "acciones": [
                        "Implementar métricas",
                        "Crear benchmark suite",
                        "Validar correctitud"
                    ]
                },
                {
                    "paso": 5,
                    "nombre": "Testing y Optimización",
                    "acciones": [
                        "Tests de performance",
                        "Optimización de memoria",
                        "Documentación final"
                    ]
                }
            ]
        }
        
        # Guardar reporte
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Reporte guardado en: {output_file}")
        
        return reporte
    
    # Métodos auxiliares
    def _leer_archivo(self, filepath: str) -> str:
        """Lee contenido de archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def _razonar(self, prompt: str, max_length: int = 2000) -> str:
        """Usa SmolLM3 para razonar"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            temperature=0.3,  # Más determinístico para código
            top_p=0.9,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def _parsear_json(self, texto: str) -> Dict:
        """Extrae JSON de texto"""
        import re
        try:
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"error": "No se pudo parsear", "raw": texto[:500]}
    
    
