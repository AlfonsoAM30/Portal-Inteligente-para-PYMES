from app.backend.llm.llm_setup import llm

class SecurityReporter:
    def __init__(self):
        pass

    def generar_informe_brechas(self, nombre_empresa, datos_brechas, stream=False):
        """
        Función encargada de generar un informa sobre los datos de brechas recibidas.
        
        [PARAMETERS]
        - datos_brechas: Lista tuplas con (email, tipo, riesgo, fecha)
        """
        
        agrupados = {}
        agrupados = {}
        for b in datos_brechas:
            email = b['email'] 
            if email not in agrupados:
                agrupados[email] = []
            agrupados[email].append({
                "tipo": b['tipo'], 
                "riesgo": b['riesgo'], 
                "fecha": b['fecha']
            })

        contexto_incidentes = ""
        for email, incidentes in agrupados.items():
            contexto_incidentes += f"USUARIO: {email}\n"
            for i in incidentes:
                contexto_incidentes += f"  - Detalle: {i['tipo']} | Severidad: {i['riesgo']} | Detectado: {i['fecha']}\n"
            
            if len(incidentes) > 1:
                contexto_incidentes += f"  ⚠️ NOTA: Este usuario presenta {len(incidentes)} vectores de ataque simultáneos.\n"
            contexto_incidentes += "\n"

        system_prompt = f"""
        Eres un CISO y Analista Forense Digital Senior de la empresa {nombre_empresa}.
        Tu objetivo es realizar un diagnóstico profundo basado en telemetría de brechas.

        REGLAS CRÍTICAS DE ANÁLISIS:
        1. IDENTIFICACIÓN DE OBJETIVOS: Si un usuario aparece con múltiples brechas, identifícalo como un "Perfil de Alto Riesgo" o "Objetivo de Interés".
        2. CORRELACIÓN: Analiza cómo la combinación de diferentes brechas (ej. Redes Sociales + Proveedores) aumenta el vector de ataque.
        3. PRECISIÓN TÉCNICA: Describe el impacto potencial de cada tipo de brecha (ej. qué significa un 'Social Media Exploit' para la empresa).
        4. FORMATO: Usa Markdown con negritas para resaltar términos técnicos y entidades.
        """

        user_prompt = f"""
        DATOS TÉCNICOS:
        ---
        {contexto_incidentes}
        ---

        INSTRUCCIONES:
        Genera un informe técnico de seguridad estrictamente limitado a las secciones indicadas. 
        PROHIBIDO añadir: introducciones, conclusiones, consejos genéricos o despedidas.

        ESTRUCTURA OBLIGATORIA:

        **Resumen**
        [Analiza brevemente la infraestructura. Si hay usuarios con múltiples brechas como en los datos, explica la correlación técnica del riesgo acumulado en máximo 4 frases.]

        **Acciones inmediatas**
        - Mitigación de Usuario: [Acciones específicas para los emails afectados]
        - Defensa Perimetral: [Acciones técnicas para IT]

        **Nivel de alerta**
        [Bajo/Medio/Alto] (Basado en el riesgo más alto detectado)
        """
        if stream:
            return llm.ask_llama_stream(system_prompt, user_prompt)
        else:
            return llm.ask_llama(system_prompt, user_prompt)
    