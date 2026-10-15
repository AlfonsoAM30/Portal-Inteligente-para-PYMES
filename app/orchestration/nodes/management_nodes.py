from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import httpx

from app.orchestration.state import State
from app.backend.llm.llm_setup import graph_llm_local
from app.core.logger import system_logger


ToolOptions = Literal[
    "view_company_data",
    "view_personal_data",
    "view_employees",
    "security_report",
    "view_budget",
    "unknown",
]

BASE_URL = "http://localhost:8091/api/management"

# =========================
# API LAYER (ROBUSTO)
# =========================
async def safe_get(client, url):
    try:
        r = await client.get(url, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        system_logger.error(f"API ERROR {url}: {str(e)}")
        return None


async def get_employees_api(empresa_id):
    async with httpx.AsyncClient() as client:
        return await safe_get(client, f"{BASE_URL}/employees/{empresa_id}")


async def get_company_api(empresa_id):
    async with httpx.AsyncClient() as client:
        return await safe_get(client, f"{BASE_URL}/company/{empresa_id}")


async def get_profile_api(empresa_id):
    async with httpx.AsyncClient() as client:
        return await safe_get(client, f"{BASE_URL}/profile/{empresa_id}")


async def get_security_api(empresa_id):
    async with httpx.AsyncClient() as client:
        return await safe_get(client, f"{BASE_URL}/breaches/{empresa_id}")


# =========================
# ROUTER
# =========================
class RouterDecision(BaseModel):
    tool_name: ToolOptions = Field(...)


async def management_node(state: State) -> dict:
    prompt_usuario = state.get("management_prompt")

    if not prompt_usuario:
        return {
            "management_tool": None,
            "management_report": "No hay comando",
        }

    system_instruction = system_instruction = """
TAREA
Analizar el mensaje o comando enviado por el usuario y determinar de forma unívoca cuál de las herramientas internas del sistema debe activarse para procesar la solicitud.

ACCIÓN
Evaluar la semántica, las palabras clave y el contexto del mensaje de entrada. Mapear dicha intención con las definiciones operativas del sistema y resolver conflictos de ambigüedad mediante las reglas de decisión explícitas.    

ROL
Eres un clasificador de intenciones de lenguaje natural y un enrutador semántico de alta precisión especializado en plataformas empresariales de gestión y ciberseguridad.

EXPECTATIVAS
- REGLA DE SALIDA ESTRICTA: Tu respuesta debe contener ÚNICA Y EXCLUSIVAMENTE el nombre exacto de la herramienta elegida en formato de texto plano (ej. view_budget).
- Queda absolutamente prohibido incluir introducciones, saludos, explicaciones de la decisión, notas, marcas de formato markdown adicionales (como comillas o negritas) o texto de relleno.
- Selecciona siempre la opción más específica posible. Si hay conflicto, prioriza la más concreta frente a la genérica.

ALCANCE
Debes clasificar la petición del usuario única y exclusivamente en una de las siguientes seis herramientas disponibles:

1. 'view_company_data': Consultas de información general o corporativa de la empresa (Nombre, dominio, teléfono, CIF, etc.).
   - Ejemplos: "datos de la empresa", "información corporativa", "teléfono de la compañía".
2. 'view_personal_data': Acceso a la propia información del usuario firmado (Perfil, datos de cuenta, configuración, IBAN).
   - Ejemplos: "mi perfil", "mis datos", "mi cuenta", "quién soy yo".
3. 'view_employees': Consultas sobre el capital humano, trabajadores o personal interno de la empresa.
   - Ejemplos: "empleados de la empresa", "lista de trabajadores", "equipo actual".
4. 'security_report': Consultas estrictamente ligadas a la seguridad, brechas, ataques, vulnerabilidades o incidentes de infraestructura.
   - Ejemplos: "brechas de seguridad", "hackeos detectados", "informe de seguridad".
5. 'view_budget': Consultas financieras, análisis de presupuestos, gastos, costes de recursos, consumo de APIs o balances económicos.
   - Ejemplos: "presupuesto de la empresa", "cuánto hemos gastado", "gasto en APIs".
6. 'unknown': Mensajes que no encajen en ninguna categoría, saludos, textos ambiguos o interacciones fuera del alcance del sistema.

REGLAS CRÍTICAS DE ENRUTAMIENTO (RESOLUCIÓN DE CONFLICTOS):
- Posesivos ("Mi"): Si el usuario antepone "mi/mis" a palabras como perfil, datos o cuenta, activa obligatoriamente 'view_personal_data'. El concepto "perfil personal" NUNCA pertenece a seguridad.
- Concepto Empresa: Las palabras "empresa" o "corporativo" (en un contexto general) se vinculan directamente con 'view_company_data'.
- Filtro de Seguridad: Activa 'security_report' ÚNICAMENTE si el contexto describe explícitamente ataques, hackeos o incidentes. Ante la más mínima duda semántica entre seguridad y otra categoría, descarta 'security_report'.
- Filtro de Dinero: Si la consulta menciona dinero, costes, facturas o gastos, selecciona obligatoriamente 'view_budget'.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{comando}")
    ])

    chain = prompt | graph_llm_local.with_structured_output(RouterDecision)

    try:
        decision = await chain.ainvoke({"comando": prompt_usuario})
        system_logger.info(f"💼 Management Router: Herramienta sugerida -> {decision.tool_name}")

        tool = decision.tool_name

        if tool == "unknown":
            return {
                "management_tool": None,
                "assistant_response": "Lo siento, no he podido clasificar tu solicitud dentro de las herramientas de gestión disponibles.",
            }

        return {
            "management_tool": tool,
            "assistant_response": None,
        }

    except Exception as e:
        system_logger.error(f"Router error: {e}")
        return {
            "management_tool": None,
            "assistant_response": "Ha ocurrido un error interno al clasificar la intención de gestión."
        }


# =========================
# TOOLS NODE (FIXED + SAFE)
# =========================
async def management_tools_node(state: State) -> dict:
    tool = state.get("management_tool")

    user_data = state.get("user_data") or {}
    auth = state.get("auth_credentials") or {}

    empresa_id = user_data.get("empresa_id")
    user_email = auth.get("email")

    system_logger.info(f"🛠️ Executing Management Tool: [{tool}] para Empresa ID: {empresa_id}")
    
    if not tool:
        return {
            "management_report": "No se seleccionó herramienta",
            "management_ui_payload": None,
        }

    ui = {
        "type": tool,
        "data": None,
        "raw_response": "",
    }

    # =========================
    # EMPLEADOS
    # =========================
    if tool == "view_employees":
        data = await get_employees_api(empresa_id)

        ui["data"] = data or []
        ui["raw_response"] = f"Se han encontrado {len(ui['data'])} empleados registrados en el sistema corporativo."

    # =========================
    # EMPRESA
    # =========================
    elif tool == "view_company_data":
        data = await get_company_api(empresa_id)

        ui["data"] = data
        ui["raw_response"] = "Información corporativa de la empresa recuperada correctamente."

    # =========================
    # PERFIL
    # =========================
    elif tool == "view_personal_data":
        perfiles = await get_profile_api(empresa_id) or []

        mi = next(
            (u for u in perfiles if u.get("email", "").lower() == (user_email or "").lower()),
            None
        )

        ui["data"] = mi
        ui["raw_response"] = (
            "Perfil cargado." if mi else "No se encontró el perfil."
        )

    # =========================
    # SEGURIDAD
    # =========================
    elif tool == "security_report":
        data = await get_security_api(empresa_id)

        if not data:
            ui["raw_response"] = "No se pudo obtener el reporte."
        else:
            ui["data"] = data
            ui["raw_response"] = f"{data.get('breach_count', 0)} brechas detectadas."

    # =========================
    # PRESUPUESTO
    # =========================
    elif tool == "view_budget":
        # Indicamos un diccionario inicial para que 'datos is None' sea falso en el frontend
        # y permita a la vista encargarse de la creación/lectura en DB.
        ui["data"] = {"status": "init_from_frontend"}
        ui["raw_response"] = "Cargando panel de control presupuestario..."

    # =========================
    # OUTPUT NORMALIZADO (IMPORTANTE)
    # =========================
    return {
        "management_tool": None,
        "management_report": ui["raw_response"],
        "management_ui_payload": ui,

        "agent_response": ui["raw_response"],
        "data": ui["data"],
    }