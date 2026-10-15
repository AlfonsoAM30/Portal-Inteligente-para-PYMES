import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# Endpoint de tu microservicio donde corre Stable Diffusion de manera local (e.g., con Diffusers o AUTOMATIC1111 de fondo)
URL_LOCAL_GENERATION = "http://localhost:8092/api/design/generate-local"

async def local_node(state: State) -> dict:
    """
    Nodo ejecutor para la generación visual utilizando hardware local (Docker 8092).
    Consume los prompts optimizados y la máscara generada por SAM.
    """
    if state.get('assistant_response') and "http" in state.get('assistant_response').lower():
        system_logger.info("Local Node: [Bypass] La imagen ya existe en el estado.")
        return {}

    if state.get('error'):
        system_logger.warning("Local Node: Abortando generación local por error previo.")
        return {}

    # Extraemos el cargamento guardado en Postgres
    image_url = state.get('product_image_url')
    mask_path = state.get('mask_path')
    positive_prompt = state.get('positive_prompt')
    negative_prompt = state.get('negative_prompt')

    if not all([image_url, mask_path, positive_prompt, negative_prompt]):
        system_logger.error("Local Node: Faltan parámetros críticos para el inpainting local.")
        return {"error": "Insumos insuficientes para la generación local."}

    try:
        system_logger.info("Local Node: Iniciando renderizado local en el MS de Diseño (Cuda/CPU)...")
        
        payload = {
            "image": image_url,
            "mask_path": mask_path,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(URL_LOCAL_GENERATION, json=payload)

        if response.status_code == 200:
            data = response.json()
            local_image_path = data.get("generated_img_url")
            if local_image_path:
                system_logger.success(f"Local Node: ¡Inpainting local completado! Archivo -> {local_image_path}")
                return {
                    "assistant_response": f"¡Diseño local terminado!",
                    "generated_img_url": local_image_path,
                    "error": None
                }
            else:
                system_logger.error("Local Node: El servicio respondió 200 pero 'generated_img_url' vino vacío.")
                return {"error": "El motor visual no devolvió ninguna URL válida."}
        else:
            system_logger.error(f"Local Node: El servicio local dio error HTTP {response.status_code}")
            return {"error": f"Fallo en Stable Diffusion Local: Código {response.status_code}"}

    except Exception as e:
        system_logger.error(f"Local Node: Error conectando con el motor local del puerto 8092: {e}")
        return {"error": f"Error en el entorno de generación local: {str(e)}"}