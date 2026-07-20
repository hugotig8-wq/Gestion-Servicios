from smollm_agent import agent
import json

class CodeReviewAgent:
    """Revisa código y propone mejoras"""
    
    def revisar_codigo(self, codigo, lenguaje="Python"):
        """Analiza código y sugiere mejoras"""
        
        prompt = f"""
        Revisa este código {lenguaje} siguiendo mejores prácticas:
        
        ```{lenguaje}
        {codigo}
        ```
        
        Analiza:
        1. Legibilidad y claridad
        2. Rendimiento
        3. Seguridad
        4. Manejo de errores
        5. Escalabilidad
        6. Duplicación de código
        7. Testing
        
        Para cada problema, proporciona:
        - Descripción
        - Severidad (crítica/alta/media/baja)
        - Sugerencia de corrección
        - Ejemplo de código mejorado
        
        Responde en JSON.
        """
        
        resultado = agent.razonar(prompt)
        return self._parsear_json(resultado)
    
    def sugerir_mejoras(self, archivo_path, contenido):
        """Propone mejoras específicas"""
        
        prompt = f"""
        Archivo: {archivo_path}
        
        ```
        {contenido}
        ```
        
        Proporciona 3-5 mejoras ordenadas por impacto:
        
        Para cada mejora:
        1. Área (performance/seguridad/legibilidad/testing)
        2. Descripción del problema
        3. Impacto estimado
        4. Código sugerido
        5. Tiempo estimado de implementación
        
        Responde en JSON con array de mejoras.
        """
        
        resultado = agent.razonar(prompt)
        return self._parsear_json(resultado)
    
    def generar_tests(self, funcion, lenguaje="javascript"):
        """Genera tests para una función"""
        
        prompt = f"""
        Genera test cases comprehensivos para esta función {lenguaje}:
        
        ```{lenguaje}
        {funcion}
        ```
        
        Crea tests que cubran:
        1. Casos normales
        2. Casos edge
        3. Manejo de errores
        4. Validación de entrada
        
        Usa framework según lenguaje:
        - JS: Jest
        - Python: pytest
        
        Responde solo código de test.
        """
        
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

code_review_agent = CodeReviewAgent()
      
