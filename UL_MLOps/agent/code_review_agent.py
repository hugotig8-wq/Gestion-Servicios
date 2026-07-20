
import json
from agent.prompt_builder import PromptBuilder

class PyCodeReviewAgent:
    """Revisa código y propone mejoras"""

    def __init__(self, prompt_builder: PromptBuilder):
        self.prompt_builder = prompt_builder
    
    def revisar_codigo(self, codigo, lenguaje="Python"):
        """Analiza código y sugiere mejoras"""

        response = self._generate(

            prompt

        )

        try:

            data = json.loads(

                response

            )

        except json.JSONDecodeError:

            data = {

                "severity":"LOW",

                "category":"Parsing",

                "title":"Invalid JSON",

                "explanation":response,

                "suggestion":"",

                "corrected_code":None,

                "line_start":None,

                "line_end":None

            }

        return Recommendation(

            file_path=file_path,

            severity=data["severity"],

            category=data["category"],

            title=data["title"],

            explanation=data["explanation"],

            suggestion=data["suggestion"],

            corrected_code=data["corrected_code"],

            line_start=data["line_start"],

            line_end=data["line_end"]

        )
    
    def sugerir_mejoras(self, archivo_path, contenido):
        """Propone mejoras específicas"""
        
        prompt = self.prompt_builder.build_sumary(archivo_path, contenido)
        
        resultado = agent.razonar(prompt)
        return self._parsear_json(resultado)
    
    def generar_tests(self, funcion, lenguaje="python"):
        """Genera tests para una función"""
        
        prompt = self.prompt_builder.build_test(funcion, lenguaje)
        
        resultado = agent.razonar(prompt)
        return resultado
    
    def _parsear_json(self, texto):
        import re
        try:
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"error": "No se pudo parsear"}

code_review_agent = PyCodeReviewAgent()
      
