import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# La URL de tu microservicio analizador (Endpoint 2)
URL_KEYWORDS_SERVICE = "http://localhost:8093/api/analyzer/analyze-reviews"

async def keywords_extractor_node(state: State) -> dict:
    """
    Nodo que consume el Endpoint 2 del MS Analyzer para extraer
    palabras clave positivas de las reseñas del producto de forma aislada.
    """
    # 1. Si ya tenemos keywords extraídas en este hilo, hacemos un Bypass
    if state.get('positive_keywords'):
        system_logger.info("Keywords Extractor: [Bypass] Las palabras clave ya existen. Saltando.")
        return {}

    # Sacamos las reviews del estado unificado (manejando fallbacks)
    reviews = state.get('product_reviews') or []
    
    if state.get('error'):
        system_logger.warning("Keywords Extractor: Existe un error previo en el Grafo. Abortando.")
        return {}

    # Si el producto no tiene reseñas en Amazon, pasamos una lista vacía de forma segura sin colapsar
    if not reviews:
        system_logger.warning("Keywords Extractor: No hay reseñas disponibles para analizar en este producto.")
        return {"positive_keywords": []}

    try:
        system_logger.info(f"Keywords Extractor: Enviando {len(reviews)} reseñas al MS Analyzer...")
        
        # Tu modelo ReviewsReq en FastAPI espera exactamente esto: {"reviews": ["...", "..."]}
        payload = {"reviews": reviews}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(URL_KEYWORDS_SERVICE, json=payload)
            
        if response.status_code == 200:
            data = response.json()
            keywords = data.get("positive_keywords", [])
            system_logger.success(f"Keywords Extractor: Extraídas {len(keywords)} palabras clave con éxito.")
            
            return {
                "keywords_extracted": keywords,
                "error": None
            }
        else:
            system_logger.error(f"Keywords Extractor: El servicio 8093 dio error HTTP {response.status_code}")
            return {"error": f"Fallo en extractor de keywords: Código {response.status_code}"}
            
    except Exception as e:
        system_logger.error(f"Keywords Extractor: Fallo de conexión con el servicio 8093: {str(e)}")
        return {"error": f"No se pudo conectar con el motor de análisis de texto: {str(e)}"}