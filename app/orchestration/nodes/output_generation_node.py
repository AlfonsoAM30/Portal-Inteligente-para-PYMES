from langchain_core.messages import AIMessage

from app.orchestration.state import State
from app.core.logger import system_logger

async def output_generation_node(state: State) -> dict:
    """
    Nodo de salida final de la rama de diseño. Captura la respuesta generada
    por los ejecutores (api o local), valida su estructura y la prepara para el cliente.
    """
    system_logger.info("Output Generation Node: Procesando respuesta de salida para el usuario...")

    error_previo = state.get('error')
    if error_previo:
        system_logger.warning(f"Output Generation Node: Detectado error previo en el flujo: {error_previo}")
        salida = f"Lo siento, no he podido completar el rediseño visual debido al siguiente problema: {error_previo}"
        return {
            "assistant_response": salida,
            "messages": [AIMessage(content=salida)]
        }

    assistant_response = state.get('assistant_response')

    if not assistant_response:
        system_logger.error("Output Generation Node: No se encontró ninguna respuesta de generación en el State.")
        salida = "El proceso ha concluido pero el motor de renderizado no devolvió un mensaje válido."
        return {
            "assistant_response": salida,
            "messages": [AIMessage(content=salida)]
        }

    system_logger.success("Output Generation Node: Respuesta consolidada y lista para pantalla.")
    
    return {"assistant_response": assistant_response, "messages": [AIMessage(content=assistant_response)]}