
from smollm_agent import agent
from datetime import datetime
import json

class ImpactAgent:
    """Analiza impacto de contratos en el tiempo"""
    
    def analizar_impacto(self, contrato_actual, contrato_anterior=None):
        """Compara contratos y detecta cambios"""
        
        prompt = f"""
        Analiza el impacto de este contrato:
        
        CONTRATO ACTUAL:
        {json.dumps(contrato_actual, indent=2, ensure_ascii=False)}
        
        {'CONTRATO ANTERIOR (para comparación):' + json.dumps(contrato_anterior, indent=2, ensure_ascii=False) if contrato_anterior else 'Primera vez registrado'}
        
        Proporciona análisis en JSON con:
        1. señales_positivas: mejoras detectadas
        2. señales_negativas: deterioros detectados
        3. cambios_valor: porcentaje de cambio económico
        4. cambios_plazo: análisis de tiempo
        5. conclusión_general: mejoró/empeoró/neutral
        6. confianza: 0-100
        
        Busca patrones de:
        - Sobrecostos
        - Cambios en plazo
        - Modificaciones de alcance
        - Incumplimientos
        
        Responde en JSON válido.
        """
        
        resultado = agent.razonar(prompt)
        return self._parsear_json(resultado)
    
    def detectar_señales(self, historico_contratos):
        """Detecta señales de impacto en serie temporal"""
        
        prompt = f"""
        Analiza esta serie de contratos para detectar tendencias:
        
        {json.dumps(historico_contratos, indent=2, ensure_ascii=False)}
        
        Detecta:
        1. Tendencia general (crecimiento/decrecimiento)
        2. Puntos de inflexión críticos
        3. Patrones anómalos
        4. Entidades más afectadas
        5. Sectores con mayor impacto
        
        Responde en JSON.
        """
        
        resultado = agent.razonar(prompt)
        return self._parsear_json(resultado)
    
    def _parsear_json(self, texto):
        """Extrae JSON de texto"""
        import re
        try:
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"error": "No se pudo parsear", "raw": texto}

impact_agent = ImpactAgent()
