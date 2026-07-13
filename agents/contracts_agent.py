from smollm_agent import agent
import requests
from datetime import datetime
import json

class ContractsAgent:
    """Busca contratos en BOE y bases de datos de Colombia"""
    
    def buscar_boe(self, keywords, fecha_inicio, fecha_fin):
        """Busca en BOE oficial"""
        prompt = f"""
        Analiza contratos públicos con estos criterios:
        - Palabras clave: {keywords}
        - Periodo: {fecha_inicio} a {fecha_fin}
        - Fuente: Boletín Oficial del Estado (España)
        
        Extrae:
        1. Número de contrato
        2. Administración contratante
        3. Objeto del contrato
        4. Importe adjudicado
        5. Fecha de adjudicación
        6. Estado actual
        
        Formato: JSON
        """
        return agent.razonar(prompt)
    
    def buscar_colombia(self, keywords, fecha_inicio, fecha_fin):
        """Busca en bases de datos de Colombia"""
        prompt = f"""
        Analiza contratos públicos de Colombia:
        - Palabras clave: {keywords}
        - Periodo: {fecha_inicio} a {fecha_fin}
        - Fuentes: SECOP, DNPM, bases municipales
        
        Extrae:
        1. Número de contrato
        2. Entidad contratante
        3. Descripción del objeto
        4. Valor del contrato
        5. Modalidad de selección
        6. Contratista
        7. Estado de cumplimiento
        
        Formato: JSON
        """
        return agent.razonar(prompt)
    
    def procesar_resultados(self, raw_data):
        """Limpia y estructura los datos"""
        try:
            return json.loads(raw_data)
        except:
            return {"error": "No se pudo parsear", "raw": raw_data}

contracts_agent = ContractsAgent()
