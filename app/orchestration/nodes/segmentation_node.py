import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# La URL exacta de tu servicio de segmentación mejorado en el puerto 8092
URL_SEGMENTATION_V2 = "http://localhost:8092/api/design/segment-image-v2"

async def segmentation_node(state: State) -> dict:
    """
    Nodo que consume la versión avanzada de segmentación (V2) enviando
    la imagen, la descripción y los metadatos visuales de CLIP.
    """
    # 1. Bypass por si ya tenemos la máscara generada en este hilo
    if state.get('mask_path'):
        system_logger.info("Segmentation Node V2: [Bypass] La máscara ya existe. Saltando.")
        return {}

    image_url = state.get('product_image_url')
    description = state.get('product_description') or ""
    visual_metadata = state.get('metadata_extracted') or [] 

    if state.get('error') or not image_url:
        system_logger.warning("Segmentation Node V2: No hay imagen base o existe un error previo.")
        return {}

    try:
        system_logger.info(f"Segmentation Node V2: Enviando imagen y contexto de CLIP al MS de Diseño...")
        
        # Mapeamos el payload exactamente como lo pide tu esquema Seg_v2Req
        payload = {
            "image": image_url,
            "description": description,
            "visual_metadata": visual_metadata
        }
        
        # Le damos un timeout generoso de 90 segundos porque los modelos de visión (SAM/Transformers) pesan lo suyo
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(URL_SEGMENTATION_V2, json=payload)
            
        if response.status_code == 200:
            data = response.json()
            mask_path = data.get("mask_path")
            system_logger.success(f"Segmentation Node V2: ¡Máscara guardada con éxito en: {mask_path}!")
            
            return {
                "mask_path": mask_path
            }
        else:
            system_logger.error(f"Segmentation Node V2: El servicio 8092 dio error HTTP {response.status_code}")
            return {"error": f"Fallo en segmentación V2: Código {response.status_code}"}
            
    except Exception as e:
        system_logger.error(f"Segmentation Node V2: Fallo de conexión con el servicio 8092: {str(e)}")
        return {"error": f"No se pudo conectar con el motor de segmentación V2: {str(e)}"}