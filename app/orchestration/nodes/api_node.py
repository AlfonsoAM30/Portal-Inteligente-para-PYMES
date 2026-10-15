import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# Endpoint exacto de tu microservicio de diseño
URL_API_GENERATION = "http://localhost:8092/api/design/generate-api"

async def api_node(state: State) -> dict:
    """
    Nodo ejecutor que consume el servicio de generación visual por API externa.
    Mapeado exactamente para cumplir con el esquema ApiGenReq del puerto 8092.
    """
    if state.get('assistant_response') and "http" in state.get('assistant_response').lower():
        system_logger.info("API Node: [Bypass] La imagen rediseñada ya existe en el estado.")
        return {}

    if state.get('error'):
        system_logger.warning("API Node: Abortando generación por error previo en el Grafo.")
        return {}

    image_url = state.get('product_image_url')
    optimized_prompt = state.get('descriptive_prompt')

    # Validación de control antes de hacer la llamada de red
    if not image_url or not optimized_prompt:
        system_logger.error("API Node: Faltan parámetros requeridos (product_image_url o descriptive_prompt).")
        return {"error": "Insumos insuficientes para la generación por API."}

    try:
        system_logger.info("API Node: Solicitando inpainting al MS de Diseño vía API externa...")
        
        payload = {
            "image": image_url,
            "descriptive_prompt": optimized_prompt
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(URL_API_GENERATION, json=payload)

        if response.status_code == 200:
            data = response.json()
            final_image_url = data.get("generated_img_url")

            if final_image_url:
                system_logger.success(f"API Node: ¡Imagen renderizada con éxito! URL -> {final_image_url}")
                return {
                    "assistant_response": "¡Tu diseño visual está listo!",
                    "generated_img_url": final_image_url,
                    "error": None
                }
            else:
                system_logger.error("API Node: El servicio respondió 200 pero 'generated_img_url' vino vacío.")
                return {"error": "El motor visual no devolvió ninguna URL válida."}
        else:
            system_logger.error(f"API Node: El servicio 8092 respondió con error HTTP {response.status_code}")
            return {"error": f"Fallo en la API de generación: Código {response.status_code}"}

    except Exception as e:
        system_logger.error(f"API Node: Fallo crítico de conexión con el endpoint de diseño: {str(e)}")
        return {"error": f"No se pudo conectar con el servicio de generación remota: {str(e)}"}