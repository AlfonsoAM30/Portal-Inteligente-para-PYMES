import json
from app.backend.llm.llm_setup import llm

class YoloTargetExtractor:
    def __init__(self):
        pass

    def get_search_prompts(self, old_description: str, clip_metadata: list) -> list:
        system_prompt = """
        Estás actuando bajo el marco metodológico TAREA.

        - TAREA: Identificar el objeto físico principal en una fotografía de e-commerce y generar una red de búsqueda.
        - ACCIÓN: Analizar la descripción del producto y las etiquetas visuales para deducir qué objeto físico es el protagonista.
        - ROL: Eres un experto en Visión Computacional.
        - EXPECTATIVAS:
            1. IGNORA conceptos abstractos, emociones, marcas, colores o piezas de embalaje (ej. ignora "elegante", "Chanel", "caja", "envoltorio").
            2. Define el objeto físico en INGLÉS utilizando palabras genéricas (ej. "sneaker", "perfume bottle", "laptop").
            3. Genera entre 5 y 7 sinónimos físicos directos para ese objeto.
        - ALCANCE: Tu salida debe ser ÚNICAMENTE un array plano (1D array) en formato JSON.
            * PROHIBIDO usar listas anidadas o listas de listas.
            * CORRECTO: ["fitness tracker", "smartwatch", "digital watch"]
            * INCORRECTO: [["fitness tracker"], ["smartwatch"], ["digital watch"]]
            * INCORRECTO: ```json ["fitness tracker"] ```
        """

        user_prompt = f"""
        Genera el array JSON de objetivos físicos basándote en:

        [DATOS DEL PRODUCTO]
        - Descripción Comercial: {old_description}
        - Etiquetas Visuales (CLIP): {', '.join(clip_metadata)}

        Salida esperada (solo array JSON):
        """

        try:
            raw_response = llm.ask_llama(system_prompt, user_prompt)

            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").replace("```", "").strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response.replace("```", "").strip()

            target_list = json.loads(raw_response)

            if not isinstance(target_list, list):
                raise ValueError("El LLM no devolvió una lista válida.")
                
            return target_list
            
        except Exception as e:
            return ["object", "product", "item"]

        