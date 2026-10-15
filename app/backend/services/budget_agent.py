from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.backend.llm.llm_setup import graph_llm_local
from app.core.logger import system_logger


class BudgetActionDecision(BaseModel):
    chart_type: Optional[Literal["bar", "pie", "line"]] = Field(
        None, description="Tipo de gráfico solicitado por el usuario si lo menciona explícitamente."
    )
    total_budget: Optional[float] = Field(None,
                                          description="Nuevo valor para el presupuesto total si se solicita modificar.")
    spent: Optional[float] = Field(None, description="Nuevo valor para lo gastado si se solicita modificar.")
    api_costs: Optional[float] = Field(None, description="Nuevo valor para los costes de API si se solicita modificar.")
    misc: Optional[float] = Field(None, description="Nuevo valor para gastos varios si se solicita modificar.")


async def analyze_budget_command(command: str) -> BudgetActionDecision:
    """Analiza comandos en lenguaje natural para controlar la UI y los datos del budget."""

    system_instruction = """
TAREA DEL SISTEMA

Eres un clasificador de intenciones y extractor de parámetros experto en gestión presupuestaria corporativa. Tu objetivo es analizar el comando del usuario y rellenar la estructura de datos requerida para actualizar la interfaz y la base de datos.

---

REGLAS DE EXTRACCIÓN DE GRÁFICO (chart_type)
- Si pide "circular", "torta", "pie", "quesito", "donat", "redondo": devuelve 'pie'.
- Si pide "lineas", "puntos", "tendencia", "evolución": devuelve 'line'.
- Si pide "barras", "columnas", "histograma": devuelve 'bar'.
- Si no menciona ningún cambio de estilo visual, deja este campo como null.

---

REGLAS DE EXTRACCIÓN DE DATOS Y VALORES
- Identifica números asociados a conceptos de dinero (Total, Gastado, API, Varios/Otros) y asígnalos al campo numérico correspondiente.
- Si el usuario usa palabras como "sube", "baja", "pon", interpreta y calcula el valor final absoluto que desea configurar.

---

REGLA CRÍTICA PARA BORRADO / REINICIO (PONER A 0)
- Si el usuario solicita "borrar todo", "eliminar todo", "limpiar datos", "poner todo a cero", "resetear presupuesto" o expresiones similares de vaciado completo:
  DEBES establecer OBLIGATORIAMENTE los campos 'total_budget', 'spent', 'api_costs' y 'misc' con el valor numérico 0.0 de manera simultánea.

---

REGLAS GENERALES DE COMPORTAMIENTO
- Si no se menciona ninguna modificación o acción sobre un campo específico (y no es una orden de borrado completo), deja dicho campo estrictamente como null.
- No inventes valores si el comando es ambiguo.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "Comando de usuario: {comando}")
    ])

    chain = prompt | graph_llm_local.with_structured_output(BudgetActionDecision)

    try:
        result = await chain.ainvoke({"comando": command})
        system_logger.info(f"🤖 Budget Agent procesó con éxito: {result}")
        return result
    except Exception as e:
        system_logger.error(f"Error en el agente de presupuesto: {e}")
        return BudgetActionDecision()