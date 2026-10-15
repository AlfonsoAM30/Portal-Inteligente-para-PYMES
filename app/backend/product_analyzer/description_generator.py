from app.backend.llm.llm_setup import llm

class DescriptionGenerator:
    def __intit__(self):
        pass

    def generate_new_product_description(self, emp_name, old_description, visual_metadata, positive_keywords, tone):
        """
        Función encargada de hacer uso de un LLM para generar una nueva descripción 
        de un producto explotando el máximo posible los puntos positivos de las reseñas
        y manteniendonos fieles a los metadatos visuales y a la anterior descripción.
        """

        system_prompt = """
        Estás actuando bajo el marco metodológico TAREA para la generación de contenido:

        - TAREA: Reescribir y optimizar la descripción comercial de un producto en un formato narrativo continuo.
        - ACCIÓN: Redactar un texto persuasivo, fluido y atractivo que fusione la información técnica y la prueba social en un único bloque de texto sin interrupciones visuales.
        - ROL: Eres un Copywriter Experto en E-commerce y Marketing Digital.
        - EXPECTATIVAS: 
            1. FORMATO ESTRICTO: Redacta la descripción en un único párrafo continuo (o máximo dos párrafos cohesionados). QUEDA TOTALMENTE PROHIBIDO el uso de listas, viñetas (bullet points), guiones, citas textuales o subtítulos.
            2. INTEGRACIÓN ORGÁNICA: Entrelaza las 'Palabras Clave Positivas' dentro de la redacción de forma natural. No menciones explícitamente a los clientes (evita frases como "los clientes dicen" o "según las reseñas"). Convierte esos puntos fuertes en beneficios narrados directamente al comprador (ej. "disfrutarás de un gran olor y una duración óptima durante todo el día...").
            3. FIDELIDAD: Mantén absoluta fidelidad a la 'Descripción Original' y a los 'Metadatos Visuales'. No inventes características, materiales o funcionalidades.
            4. TONO: Adapta el lenguaje estrictamente al 'Tono' solicitado, enfocándote en la conversión y la venta emocional.
        - ALCANCE: Tu salida debe ser ÚNICAMENTE el párrafo final redactado. No incluyas saludos, confirmaciones, ni encabezados.
        """

        user_prompt = f"""
        Genera la nueva descripción comercial en un bloque de texto narrativo basándote en los siguientes datos:

        - Nombre de la Empresa vendedora: {emp_name}
        - Tono e instrucción de redacción: {tone}
        
        [DATOS DEL PRODUCTO]
        - Descripción Original: {old_description}
        - Metadatos Visuales (Apariencia real): {visual_metadata}
        - Palabras Clave Positivas (Puntos fuertes a integrar en el texto): {positive_keywords}

        Redacta la descripción final a continuación:
        """

        return llm.ask_llama(system_prompt, user_prompt)
