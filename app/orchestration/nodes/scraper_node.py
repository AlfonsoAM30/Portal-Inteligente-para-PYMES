import httpx
from langchain_core.messages import AIMessage

from app.orchestration.state import State
from app.core.logger import system_logger
from app.orchestration.state import State

URL_SCRAPPER_SERVICE = "http://localhost:8095/api/scraper/product"
async def scraper_node(state: State) -> dict:
    if state.get('product_image_url'):
        system_logger.info("Scraper Node: [Bypass] El producto ya está scrapeado. Saltando ejecución.")
        return {}

    url = state.get('product_prompt')

    if not state.get('error') and url:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    URL_SCRAPPER_SERVICE,
                    params={"url": url}
                )
            
            if response.status_code == 200:
                data = response.json()
                system_logger.success("Scraper Node: Datos recibidos del microservicio 8095 con éxito.")

                return {
                    "product_image_url": data.get('image', ''),
                    "product_description": data.get('description', ''),
                    "product_reviews": data.get('reviews', ''),
                    "error": None,
                    "messages": [AIMessage(content="Producto analizado correctamente. ¿Qué diseño o análisis quieres que haga?")]
                }
            
            elif response.status_code == 404:
                system_logger.warning("Scraper Node: El microservicio no encontró el producto.")
                return {"error": "No se pudo extraer la información de esta tienda. Verifica el enlace."}
            else:
                system_logger.error(f"Scraper Node: Error del servicio 8095. Código {response.status_code}")
                return {"error": f"El servicio de extracción respondió con error {response.status_code}"}
            
        except Exception as e:
            system_logger.error(f"Scraper Node: Fallo de conexión con el servicio 8095: {str(e)}")
            return {"error": f"No se pudo conectar con el motor de extracción: {str(e)}"}
    else:
        system_logger.info("Scraper Node: El mensaje no contiene una URL válida.")
        return {"error": "Por favor, introduce una URL válida para comenzar."}
