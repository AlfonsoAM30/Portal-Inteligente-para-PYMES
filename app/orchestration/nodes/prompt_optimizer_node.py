import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# La URL de tu microservicio que ya tiene el endpoint listo
URL_PROMPT_OPTIMIZER = "http://localhost:8092/api/design/optimize-prompt"

async def prompt_optimizer_node(state: State) -> dict:
    """
    Nodo que consume el Endpoint de optimización de prompts en el MS Analyzer
    para traducir la idea del usuario en directivas de Stable Diffusion.
    """
    # 1. Bypass por si ya ha sido procesado en este hilo
    if state.get('positive_prompt'):
        system_logger.info("Prompt Optimizer: [Bypass] Los prompts ya están optimizados.")
        return {}

    user_idea = state.get('design_prompt')
    description = state.get('product_description') or ""

    if state.get('error') or not user_idea:
        system_logger.warning("Prompt Optimizer: No hay idea de diseño o existe un error previo.")
        return {}

    try:
        system_logger.info(f"Prompt Optimizer: Solicitando expansión de prompt para: '{user_idea}'...")
        
        payload = {
            "user_idea": user_idea,
            "description": description
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(URL_PROMPT_OPTIMIZER, json=payload)
            
        if response.status_code == 200:
            data = response.json()
            system_logger.success("Prompt Optimizer: Súper-prompts generados con éxito para Stable Diffusion.")
            
            return {
                "positive_prompt": data.get("positive_prompt"),
                "negative_prompt": data.get("negative_prompt"),
                "descriptive_prompt": data.get("descriptive_prompt"),
            }
        else:
            system_logger.error(f"Prompt Optimizer: El servicio 8092 dio error {response.status_code}")
            return {"error": f"Fallo en optimizador de prompt: Código {response.status_code}"}
            
    except Exception as e:
        system_logger.error(f"Prompt Optimizer: Fallo de conexión con el servicio 8092: {str(e)}")
        return {"error": f"No se pudo conectar con el optimizador de prompts: {str(e)}"}