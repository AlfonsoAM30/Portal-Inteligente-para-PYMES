from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.orchestration.state import State
from app.core.logger import system_logger

from app.orchestration.nodes.scraper_node import scraper_node
from app.orchestration.nodes.metadata_extractor_node import metadata_extractor_node
from app.orchestration.nodes.product_llm_node import product_llm_node
from app.orchestration.nodes.keywords_extractor_node import keywords_extractor_node
from app.orchestration.nodes.output_new_description_node import output_new_description_node 
from app.orchestration.nodes.prompt_optimizer_node import prompt_optimizer_node
from app.orchestration.nodes.segmentation_node import segmentation_node
from app.orchestration.nodes.api_node import api_node
from app.orchestration.nodes.local_node import local_node
from app.orchestration.nodes.output_generation_node import output_generation_node
from app.orchestration.nodes.management_nodes import management_node, management_tools_node
from app.orchestration.nodes.auth_node import auth_node

# --- NODOS MOCK (Se limitan a continuar con el flujo) ---
async def mock_node(state: State) -> dict:
    return {}

selection_node = mock_node
generation_orchestrator_node = mock_node
generator_node = mock_node

def route_selection(state: State) -> str:
    "Función que decide si ir a 'Diseño' o 'Management'"
    option = state.get('functional_option')
    if option == "management":
        return "management"
    elif option == 'design':
        return "design"
    elif option == "selection":
        system_logger.info("Router [Selection]: Modo espera, esperando usuario.")
        return "end"
    else:
        system_logger.error(f"Opción de enrutamiento no válida: {option}")
        return "end" 

def route_management(state: State) -> str:
    "Función que decide que hacer en el nodo Management"
    
    if state.get("functional_option") == "exit":
        return "end"

    selected_tool = state.get('management_tool')
    if selected_tool is None:
        return 'loop'
    else:
        return 'tool_usage'

def router_llm_designer(state: State) -> str:
    "Función que en el nodo LLM Designer decide si ir a Entorno, Descripción"
    user_intention = state.get('user_intention')
    if user_intention is None:
        return "end"
    
    if user_intention == "new_enviroment":
        return "new_enviroment"
    elif user_intention == "analysis":
        return "analysis"
    elif user_intention == "new_product":
        return "new_product"
    else:
        system_logger.error(f"Opción de enrutamiento no válida: {user_intention}")
        return "end"


def route_generator(state: State) -> str:
    "Función que decide que tipo de modelo de generación usar"
    return 'api'    # De momento usamos la versión de api siempre hasta que se consiga optimizar la ejecución del modelo local

def route_continue_or_end(state: State) -> str:
    "Función que decide si despues de la salida volver al LLM Designer o acabar"
    return 'again'


builder = StateGraph(State)

# --- 1. Definición de Nodos 
builder.add_node("auth", auth_node)
builder.add_node("selection", selection_node)

builder.add_node("management", management_node)
builder.add_node("management_tools", management_tools_node)

builder.add_node("scraper", scraper_node)
builder.add_node("product_llm", product_llm_node)
builder.add_node("generation_orchestrator", generation_orchestrator_node)
builder.add_node("segmentator", segmentation_node)
builder.add_node("prompt_optimizer", prompt_optimizer_node)
builder.add_node("generator", generator_node)
builder.add_node("api", api_node)
builder.add_node("local", local_node)
builder.add_node("output_generation", output_generation_node)

builder.add_node("metadata_extractor", metadata_extractor_node)
builder.add_node("keywords_extractor", keywords_extractor_node)
builder.add_node("new_description_output", output_new_description_node)


# --- 2. Generación de conexiones entre nodos
builder.add_edge(START, "auth")
builder.add_edge("auth", "selection")

# ---2.1 Selección de tarea
builder.add_conditional_edges(
    "selection",
    route_selection,
    {
        "design": "scraper",
        "management": "management",
        "end": END
    }
)

# --- 2.2 Logíca del nodo management (Usar tools, repetir o acabar ejecución)
builder.add_conditional_edges(
    "management",
    route_management,
    {
        "tool_usage": "management_tools",
        "loop": "management",
        "end": END
    }
)
builder.add_edge("management_tools", "management")


# --- 2.3 Lógica del nodo de diseño 
builder.add_edge("scraper", "metadata_extractor")
builder.add_edge("metadata_extractor", "product_llm")
builder.add_conditional_edges(
    "product_llm",
    router_llm_designer,
    {
        "new_enviroment": "generation_orchestrator",
        "analysis": "keywords_extractor",
        "new_product": "scraper",
        "end": END
    }
)

# --- 2.4 Lógica de la sub-rama de generación de nuevo entorno
builder.add_edge("generation_orchestrator", "segmentator")
builder.add_edge("generation_orchestrator", "prompt_optimizer")
builder.add_edge("segmentator", "generator")
builder.add_edge("prompt_optimizer", "generator")
builder.add_conditional_edges(
    "generator",
    route_generator,
    {
        "api": "api",
        "local": "local"
    }
)
builder.add_edge("api", "output_generation")
builder.add_edge("local", "output_generation")
builder.add_conditional_edges(
    "output_generation",
    route_continue_or_end,
    {
        "again": "product_llm",
        "end": END
    }
)

# --- 2.5 Lógica de la sub-rama de analisis del producto
builder.add_edge("keywords_extractor", "new_description_output")
builder.add_conditional_edges(
    "new_description_output",
    route_continue_or_end,
    {
        "again": "product_llm",
        "end": END
    }
)

# --- 3. Compilación del grafo
def compile_graph(memory: AsyncPostgresSaver):
    """
    Recibe la conexión a PostgreSQL desde FastAPI y compila el grafo.
    """
    app_graph = builder.compile(
        checkpointer=memory,
        interrupt_before=[
            "management", 
            "product_llm"
        ]
    )
    return app_graph



