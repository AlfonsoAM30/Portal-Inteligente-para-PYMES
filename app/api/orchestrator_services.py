import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional, List
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langfuse.langchain import CallbackHandler

from langchain_core.messages import HumanMessage

from dotenv import load_dotenv
load_dotenv()
from app.orchestration.graph import compile_graph
from app.core.logger import system_logger

DB_URI = os.getenv("DATABASE_URL")

langfuse_handler = CallbackHandler()

pool = None
graph_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool, graph_app
    system_logger.info("Orquestador: Inicializando pool de conexiones con Postgres...")
    try:
        pool = AsyncConnectionPool(conninfo=DB_URI, max_size=10, open=False)
        await pool.open()
        
        checkpointer = AsyncPostgresSaver(pool)
        async with pool.connection() as conn:
            await conn.set_autocommit(True)
            await conn.execute("SELECT 1")
        
        await checkpointer.setup()
        graph_app = compile_graph(checkpointer)
        system_logger.info("Orquestador: ¡Grafo compilado con éxito y listo para la acción!")
    except Exception as e:
        system_logger.error(f"Error crítico durante el arranque del orquestador: {str(e)}")
        raise e
    yield
    if pool:
        await pool.close()
        system_logger.info("Orquestador: Pool de conexiones cerrado limpiamente.")


app = FastAPI(title="AI Orchestrator Service - TELEMETRY EDITION", lifespan=lifespan)

class ChatPayload(BaseModel):
    user_message: str
    thread_id: str
    reset_state: bool = False
    functional_option: Literal["design", "management", "selection"] = "design"
    product_prompt: Optional[str] = None
    design_prompt: Optional[str] = None
    management_prompt: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    user_intention: Optional[str] = None 
    product_image_url: Optional[str] = None
    product_description: Optional[str] = None
    product_reviews: Optional[List[str]] = None

@app.post("/api/orchestrator/chat")
async def handle_chat_request(payload: ChatPayload):
    if not graph_app:
        system_logger.critical("🚨 Solicitud rechazada: El Grafo no está compilado en el lifespan.")
        raise HTTPException(status_code=503, detail="Grafo no inicializado.")
        
    config = {"configurable": {"thread_id": payload.thread_id}, "callbacks": [langfuse_handler]}
    user_email = payload.thread_id
    
    system_logger.info(f"📥 Nueva petición HTTP recibida para el hilo: {user_email} | Opción solicitada: {payload.functional_option}")


    if "_slot_" in user_email:
        try:
            email_original = user_email.split("_slot_")
            config_original = {"configurable": {"thread_id": email_original}, "callbacks": [langfuse_handler]}
            
            estado_slot_actual = await graph_app.aget_state(config)
            
            if not estado_slot_actual.values or not estado_slot_actual.values.get("messages"):
                system_logger.warning(f"🔮 Espejo LangGraph: Detectado slot nuevo virgen '{user_email}'. Buscando pasado en '{email_original}'...")
                
                estado_original = await graph_app.aget_state(config_original)
                
                if estado_original.values and estado_original.values.get("messages"):
                    mensajes_padre = estado_original.values.get("messages")
                    system_logger.success(f"📦 Copiando {len(mensajes_padre)} mensajes históricos del lienzo principal hacia el checkpoint del slot.")
                    
                    clon_estado = {
                        "messages": mensajes_padre,
                        "logged": estado_original.values.get("logged", True),
                        "user_data": estado_original.values.get("user_data"),
                        "auth_credentials": estado_original.values.get("auth_credentials"),
                        "product_prompt": estado_original.values.get("product_prompt"),
                        "product_image_url": estado_original.values.get("product_image_url"),
                        "product_description": estado_original.values.get("product_description"),
                        "product_reviews": estado_original.values.get("product_reviews"),
                        "matadata_extracted": estado_original.values.get("matadata_extracted"),
                        "current_status": "START"
                    }
                    
                    await graph_app.aupdate_state(config, clon_estado, as_node="auth")
                    
        except Exception as err_mirror:
            system_logger.error(f"⚠️ Error no crítico en el espejo de hilos LangGraph: {err_mirror}")

    if payload.reset_state:
        system_logger.warning(f"🧹 Orquestador: Reseteando contexto de trabajo para el hilo {user_email}")
        
        current_state = await graph_app.aget_state(config)
        user_data_guardado = current_state.values.get("user_data") if current_state.values else None
        auth_credentials_guardado = current_state.values.get("auth_credentials") if current_state.values else None

        if payload.reset_state:
            active_option = payload.functional_option
            auth_credentials_guardado = {
                "email": payload.email or user_email,
                "password": payload.password,
            }

        vaciar_estado = {
            "logged": current_state.values.get("logged", False) if current_state.values else False,
            "auth_credentials": auth_credentials_guardado,
            "user_data": user_data_guardado,
            
            "current_status": "START",
            "functional_option": payload.functional_option,
            "assistant_response": None,
            
            "management_prompt": None, "management_tool": None, "management_report": None, "management_ui_payload": None,
            
            # Limpieza rama creativa (Aseguramos limpiar la lista de mensajes en el reset completo)
            "messages": [],
            "product_prompt": payload.product_prompt,
            "design_prompt": None, "user_intention": None,
            "product_image_url": None, "product_description": None, "product_reviews": None,
            "matadata_extracted": None, "mask_path": None, "positive_prompt": None, "negative_prompt": None,
            "descriptive_prompt": None, "generated_img_url": None, "keywords_extracted": None, "analysis_result": None, "error": None
        }

        await graph_app.aupdate_state(config, vaciar_estado, as_node="auth")
        system_logger.success(f"✅ Estado inicializado y limpio en Postgres firmando como [auth]")
    
    try:
        system_logger.info(f"🔍 Leyendo checkpoint actual en Postgres para el hilo {user_email}...")
        current_state = await graph_app.aget_state(config)
        
        if current_state.values:
            system_logger.info(
                f"📊 Checkpoint encontrado en DB -> "
                f"Siguiente nodo en cola: {current_state.next} | "
                f"user_intention guardado: '{current_state.values.get('user_intention')}' | "
                f"product_prompt en DB: {'Sí' if current_state.values.get('product_prompt') else 'No'}"
            )
        else:
            system_logger.info("ℹ️ No hay registros previos en la base de datos para este hilo (Hilo virgen).")

        es_reanudacion = current_state.values is not None and not payload.reset_state

        active_option = payload.functional_option
        
        if not active_option and current_state.values:
            active_option = current_state.values.get("functional_option")

        user_data_state = current_state.values.get("user_data") if current_state.values else None
        auth_credentials_state = current_state.values.get("auth_credentials") if current_state.values else None

        if active_option == "management":
            system_logger.info("💼 Preparando payload para la rama MANAGEMENT...")
            payload_estado = {
                "functional_option": "management",
                "management_prompt": payload.management_prompt,
                "user_data": user_data_state,
                "auth_credentials": auth_credentials_state
            }
        elif active_option == "selection":
            system_logger.info(f"🔀 Orquestador: Manteniendo el HUB DE SELECCIÓN para el hilo {user_email}")
            payload_estado = {
                "functional_option": "selection",
                "user_data": user_data_state,
                "auth_credentials": auth_credentials_state
            }
        else:
            system_logger.info("🎨 Preparando payload para la rama DESIGN...")
            if es_reanudacion:
                payload_estado = {
                    "functional_option": "design",
                    "design_prompt": payload.design_prompt,
                    "user_data": user_data_state,
                    "auth_credentials": auth_credentials_state
                }
                
                if payload.user_intention == "wait":
                    system_logger.info("⏳ Orquestador: Reanudación visual pasiva desde Sidebar. Evitando alterar histórico.")
                    payload_estado["user_intention"] = "wait"
                    payload_estado["user_message"] = None
                
                else:
                    system_logger.info(f"💬 Orquestador: Añadiendo nuevo mensaje del usuario al historial: '{payload.user_message}'")
                    payload_estado["user_intention"] = None  # Permitimos re-evaluación del LLM
                    payload_estado["messages"] = [HumanMessage(content=payload.user_message)]
            else:
                system_logger.info("🚀 Orquestador: Inicializando Turno 1 (Carga limpia de Scraper).")
                payload_estado = {
                    "functional_option": "design",
                    "product_prompt": payload.product_prompt,
                    "design_prompt": None,
                    "user_intention": None,
                    "user_data": user_data_state,
                    "auth_credentials": auth_credentials_state,
                    "messages": [HumanMessage(content=payload.user_message)]
                }

        if es_reanudacion:
            nodo_firma = "management" if active_option == "management" else "metadata_extractor"
            system_logger.info(f"💾 Guardando parche en Postgres simulando firma del nodo [{nodo_firma}]...")
            await graph_app.aupdate_state(config, payload_estado, as_node=nodo_firma)
            initial_input = None
            system_logger.success(f"🔄 Orquestador: Hilo reanudado de forma segura. Avanzando desde la interrupción.")
        else:
            system_logger.info("💾 Guardando estado de arranque en Postgres simulando firma del nodo [auth]...")
            
            payload_estado["auth_credentials"] = {
                "email": payload.email or user_email,
                "password": payload.password,
            }
            
            await graph_app.aupdate_state(config, payload_estado, as_node="auth")
            
            initial_input = payload_estado
            system_logger.success("🚀 Orquestador: Lanzando ejecución limpia desde el nodo START.")


        if payload.product_description or payload.product_image_url:
            system_logger.warning("📥 Orquestador: Forzando inyección de contexto de producto en Postgres...")
            update_data = {}
            if payload.product_prompt: update_data["product_prompt"] = payload.product_prompt
            if payload.product_image_url: update_data["product_image_url"] = payload.product_image_url
            if payload.product_description: update_data["product_description"] = payload.product_description
            if payload.product_reviews: update_data["product_reviews"] = payload.product_reviews
            
            await graph_app.aupdate_state(config, update_data, as_node="metadata_extractor")

        if payload.user_intention == "wait":
            system_logger.success("🛑 [CORTOCUITO SIDEBAR] Retornando estado actual directamente desde Postgres sin activar el Grafo.")
            graph_state = await graph_app.aget_state(config)
            return {
                "status": "success",
                "state": graph_state.values
            }

        system_logger.info("🎬 Encendiendo motor de ejecución del Grafo (astream)...")
        
        async for event in graph_app.astream(initial_input, config, stream_mode="updates"):
            if not event or not isinstance(event, dict):
                continue
                
            for nodo_ejecutado, variables_modificadas in event.items():
                system_logger.success(f"⚡ [NODO TERMINADO] -> El nodo '{nodo_ejecutado}' acaba de ejecutarse con éxito.")
                
                if isinstance(variables_modificadas, dict):
                    system_logger.info(f"   🔧 Variables modificadas por el nodo: {list(variables_modificadas.keys())}")
                    if "user_intention" in variables_modificadas:
                        system_logger.warning(f"   🎯 ¡Cambio de Intención! -> 'user_intention' ha mutado a: '{variables_modificadas['user_intention']}'")
                    if "error" in variables_modificadas and variables_modificadas["error"]:
                        system_logger.error(f"   🚨 El nodo reportó un error interno: {variables_modificadas['error']}")

        system_logger.info("🏁 Motor de streaming finalizado. Extrayendo estado de salida resultante...")
        graph_state = await graph_app.aget_state(config)
        
        system_logger.info(
            f"📥 Estado de salida en DB -> "
            f"¿Siguiente nodo pendiente? {graph_state.next if graph_state.next else 'Ninguno (Grafo en END)'} | "
            f"Intención final: '{graph_state.values.get('user_intention')}'"
        )
            
        return {
            "status": "success",
            "state": graph_state.values
        }
        
    except Exception as e:
        system_logger.error(f"💥 Error crítico en el flujo interactivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("orchestrator_services:app", host="0.0.0.0", port=8000, reload=True)