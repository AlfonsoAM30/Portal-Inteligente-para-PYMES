import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

URL_ANALYZER_SERVICE = "http://localhost:8093/api/analyzer/extract-metadata"

async def metadata_extractor_node(state: State) -> dict:
    """
    Nodo que consume el Endpoint 1 del MS Analyzer para extraer
    las etiquetas visuales del producto usando CLIP de forma aislada.
    """
    if state.get('metadata_extracted'):
        system_logger.info("Metadata Extractor: [Bypass] Las etiquetas ya existen. Saltando.")
        return {}

    image_url = state.get('product_image_url')
    if not image_url:
        system_logger.warning("Metadata Extractor: No hay imagen disponible")
        return {}
    if state.get('error'):
        system_logger.warning("Metadata Extractor: Existe un error previo.")
        return {}

    try:
        system_logger.info(f"Metadata Extractor: Enviando imagen al MS Analyzer...")
        payload = {"image_source": image_url}
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(URL_ANALYZER_SERVICE, json=payload)
            
        if response.status_code == 200:
            data = response.json()
            system_logger.success("Metadata Extractor: Etiquetas visuales obtenidas con éxito.")
            
            # 🟢 Guardamos las etiquetas en el State mapeadas correctamente
            return {
                "matadata_extracted": data.get("visual_metadata", []),
                "error": None
            }
        else:
            system_logger.error(f"Metadata Extractor: El servicio 8093 dio error {response.status_code}")
            return {"error": f"Fallo en extractor visual: Código {response.status_code}"}
            
    except Exception as e:
        system_logger.error(f"Metadata Extractor: Fallo de conexión con el servicio 8093: {str(e)}")
        return {"error": f"No se pudo conectar con el motor de análisis visual: {str(e)}"}