import httpx
from langchain_core.messages import AIMessage

from app.orchestration.state import State
from app.core.logger import system_logger

# La URL de tu microservicio analizador (Endpoint 3)
URL_OPTIMIZE_SERVICE = "http://localhost:8093/api/analyzer/optimize-description"

async def output_new_description_node(state: State) -> dict:
    """
    Nodo final de la rama de análisis. Envía todo el contexto recopilado
    (Texto + CLIP) al MS Analyzer para generar la descripción optimizada.
    """
    # Si ya existe una descripción mejorada en este hilo, saltamos (Bypass)
    if state.get('assistant_response') and "mejorada" in state.get('assistant_response').lower():
        system_logger.info("Output Description: [Bypass] La descripción optimizada ya existe.")
        return {}

    if state.get('error'):
        system_logger.warning("Output Description: Existe un error previo. Abortando nodo.")
        return {}

    try:
        system_logger.info("Output Description: Solicitando redacción optimizada al MS Analyzer...")

        payload = {
            "name_empresa": "E-Commerce Premium", # Puedes dinamizarlo si quieres
            "current_description": state.get("product_description") or "Sin descripción original.",
            "visual_tags": state.get("metadata_extracted") or [], # ◄─ ¡Inyectamos las etiquetas de CLIP!
            "positive_keywords": state.get("keywords_extracted") or [], # ◄─ ¡Inyectamos los insights del paso anterior!
            "tone": "profesional y persuasivo"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(URL_OPTIMIZE_SERVICE, json=payload)

        if response.status_code == 200:
            data = response.json()
            enhanced_desc = data.get("enhanced_description", "No se pudo generar el texto.")
            system_logger.success("Output Description: ¡Super-Descripción generada con éxito por la IA!")

            return {
                "assistant_response": enhanced_desc,
                "analysis_result": enhanced_desc,
                "messages": [AIMessage(content=enhanced_desc)],
                "error": None
            }
        else:
            system_logger.error(f"Output Description: El servicio 8093 dio error {response.status_code}")
            return {"error": f"Fallo en optimización de descripción: Código {response.status_code}"}

    except Exception as e:
        system_logger.error(f"Output Description: Fallo de conexión con el servicio 8093: {str(e)}")
        return {"error": f"No se pudo conectar con el motor de redacción: {str(e)}"}