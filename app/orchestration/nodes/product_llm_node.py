from pydantic import BaseModel, Field
from app.orchestration.state import State
from app.core.logger import system_logger

class DesignDecision(BaseModel):
    intent: str = Field(
        description="DEBES elegir 'new_enviroment' (para crear/diseñar/cambiar fondo) o 'analysis' (para insights/opiniones/resumen de texto)."
    )

async def product_llm_node(state: State) -> dict:
    """
    Nodo encargado de procesar las interacciones de texto del usuario
    y clasificar su intención usando estructuración de salida perezosa (Lazy).
    """
    from langchain_core.prompts import ChatPromptTemplate
    from app.backend.llm.llm_setup import graph_llm_local

    prompt = state.get('design_prompt') 
    product_desc = state.get('product_description')
    
    system_logger.info(f"Product LLM: Analizando intención de diseño para el prompt: '{prompt}'")

    if not prompt:
        system_logger.warning("Product LLM: No se detectó prompt del usuario. Defectando a 'analysis'.")
        return {"user_intention": "analysis"}

    system_instruction = """
TAREA
Clasificar la petición del usuario en una de las dos categorías de negocio disponibles basándote en la semántica de su mensaje y el contexto del producto actual.    

ACCIÓN
Analizar el comando o solicitud del usuario en lenguaje natural, evaluar su intención real y etiquetarla estrictamente dentro de uno de los dos flujos operativos definidos en el ALCANCE.

ROL
Eres un experto en diseño de producto, marketing digital y un clasificador de intenciones altamente preciso.

EXPECTATIVAS
- La salida debe limitarse única y exclusivamente a la cadena de texto de la categoría elegida ('new_enviroment' o 'analysis').
- Queda estrictamente prohibido añadir texto de introducción, explicaciones, saludos, notas de desarrollo o formato adicional que no sea el identificador de la categoría.
- Si la petición es ambigua o comparte características de ambas, prioriza la intención dominante que requiera mayor carga de ejecución según el contexto proporcionado.


ALCANCE
Debes asignar la petición del usuario única y exclusivamente a una de estas dos categorías:
1. 'new_enviroment': Si el usuario quiere generar un fondo, cambiar el entorno, hacer una nueva composición visual, un diseño específico o modificar estéticamente la imagen.
2. 'analysis': Si el usuario quiere un resumen, una opinión sobre las reviews, un análisis técnico, entender los puntos fuertes del producto o cambiar/redactar el texto de la descripción.

Contexto del producto actual para la toma de decisiones:
{contexto}
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "Orden del usuario: {comando}")
    ])

    try:
        chain = prompt_template | graph_llm_local.with_structured_output(DesignDecision)
        decision = await chain.ainvoke({"contexto": product_desc, "comando": prompt})
        system_logger.success(f"Product LLM: Intención clasificada con éxito como '{decision.intent}'")
        
        return {"user_intention": decision.intent}
        
    except Exception as e:
        system_logger.error(f"Product LLM: Error en la clasificación por LLM: {str(e)}")
        return {"user_intention": "analysis"}