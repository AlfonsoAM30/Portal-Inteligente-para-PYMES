import os
import re
import traceback
import time
from nicegui import ui, run
import asyncio

from app.backend.llm.llm_setup import LLMConnection
from app.core.logger import system_logger

LOG_FILE_PATH = 'logs/system.log'
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def read_log_file_safe(path, max_lines=2000):
    if not os.path.exists(path):
        return []

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            return lines[-max_lines:]
    except Exception:
        return []


def build_log_report(log_path: str, max_lines: int = 2000):
    raw_lines = read_log_file_safe(log_path, max_lines)
    clean_lines = []

    for line in raw_lines:
        line = ANSI_ESCAPE.sub('', line).strip()
        if line:
            clean_lines.append(line)

    metrics = {
        "total_logs": len(clean_lines),
        "errors": sum(1 for l in clean_lines if "| ERROR" in l or "| CRITICAL" in l),
        "warnings": sum(1 for l in clean_lines if "| WARNING" in l),
        "success": sum(1 for l in clean_lines if "| SUCCESS" in l),
        "debug": sum(1 for l in clean_lines if "| DEBUG" in l),
        "info": sum(1 for l in clean_lines if "| INFO" in l),
    }

    return "\n".join(clean_lines), metrics


def generate_log_prompt(log_text, metrics):
    return f"""
Eres un ingeniero senior de DevOps y observabilidad.

Analiza logs estructurados de un sistema en producción.

MÉTRICAS:
- Total logs: {metrics['total_logs']}
- INFO: {metrics['info']}
- SUCCESS: {metrics['success']}
- WARNING: {metrics['warnings']}
- ERROR: {metrics['errors']}
- DEBUG: {metrics['debug']}

LOGS:
{log_text}

Devuelve:

1. Estado general del sistema
2. Salud del sistema
3. Errores críticos
4. Patrones detectados
5. Riesgos
6. Recomendaciones técnicas claras
"""


def admin_dashboard(state: dict):
    role = state.get('role') or state.get('rol')

    if not state.get('logged') or role != 'admin':
        with ui.card().classes(
                'w-full max-w-md mx-auto mt-20 p-6 shadow-xl border border-red-900 bg-red-950/30 text-center'):
            ui.icon('gpp_bad', color='red-500').classes('text-5xl mb-2')
            ui.label("Acceso denegado").classes('text-red-400 text-2xl font-bold')
            ui.label("Esta sección está reservada exclusivamente para administradores.").classes(
                'text-red-500/80 text-sm mt-1')
        return

    with ui.row().classes('w-full items-center justify-between border-b border-gray-800 pb-4 mb-4'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('analytics', color='blue-400').classes('text-3xl')
            with ui.column().classes('gap-0'):
                ui.label("Terminal de Observabilidad").classes('text-2xl font-black text-white tracking-tight')
                ui.label("Monitoreo en tiempo real y auditoría inteligente").classes('text-xs text-gray-400')

        with ui.row().classes('items-center bg-[#1a1c23] px-3 py-1.5 rounded-full border border-gray-800'):
            ui.badge('', color='green-500').classes('w-2 h-2 p-0 min-h-0 rounded-full animate-pulse mr-1')
            debug_box = ui.label("Inicializando...").classes('text-xs font-medium text-gray-300 font-mono')

    with ui.grid(columns='1fr 1fr').classes('w-full gap-6 items-start md:grid-cols-2 grid-cols-1'):

        with ui.card().classes('w-full p-4 border border-gray-800 shadow-lg rounded-xl overflow-hidden bg-[#1a1c23]'):
            with ui.row().classes('w-full justify-between items-center mb-3'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('terminal', color='gray-400').classes('text-xl')
                    ui.label("Trazas del Servidor").classes('text-base font-bold text-white')
                ui.label("Live").classes(
                    'text-[10px] uppercase tracking-widest bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded-md font-bold border border-emerald-800/50')

            log_container = ui.scroll_area().classes(
                'w-full h-[500px] bg-[#0c0d12] p-4 rounded-lg font-mono text-xs shadow-inner border border-gray-900'
            )

            with log_container:
                log_view = ui.column().classes('w-full gap-0.5')

        with ui.column().classes('w-full gap-4'):
            # Sub-tarjeta de Métricas rápidas
            with ui.card().classes('w-full p-4 border border-gray-800 shadow-md rounded-xl bg-[#1a1c23]'):
                ui.label("Resumen de Contramedidas").classes(
                    'text-xs font-bold uppercase tracking-wider text-gray-400 mb-2')
                metrics_box = ui.label("Esperando análisis...").classes('text-sm text-gray-200 font-medium')

            # Tarjeta de Generación de Reportes con LLM (UNA SOLA CAJA)
            with ui.card().classes('w-full p-4 border border-gray-800 shadow-md rounded-xl bg-[#1a1c23]'):
                with ui.row().classes('w-full items-center gap-2 mb-3'):
                    ui.icon('psychology', color='blue-400').classes('text-2xl')
                    ui.label("Auditoría de IA Devops").classes('text-base font-bold text-white')

                with ui.scroll_area().classes('w-full h-[320px] bg-[#0c0d12] p-4 rounded-lg border border-gray-900 overflow-y-auto'):
                    report_box = ui.markdown(
                        'El informe de auditoría generado por la IA aparecerá aquí tras analizar las trazas...'
                    ).classes('text-sm text-gray-200 markdown-body')

                ui.button(
                    "Generar diagnóstico con IA",
                    on_click=lambda: on_generate_report(),
                    icon='analytics'
                ).classes(
                    "w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-700 text-white font-bold rounded-lg shadow-md hover:from-blue-700 hover:to-indigo-800 transition-all text-sm uppercase tracking-wider")


    cursor = {'position': None}

    async def update_ui_logs():
        try:
            if not os.path.exists(LOG_FILE_PATH):
                debug_box.text = "Error: Archivo no encontrado"
                return

            with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='replace') as f:
                if cursor['position'] is None:
                    f.seek(0, os.SEEK_END)
                    cursor['position'] = f.tell()
                    return

                f.seek(cursor['position'])
                new_lines = f.readlines()
                cursor['position'] = f.tell()

            for line in new_lines:
                clean_line = ANSI_ESCAPE.sub('', line).strip()
                if not clean_line:
                    continue

                with log_view:
                    if "| ERROR" in clean_line or "| CRITICAL" in clean_line:
                        color = 'text-red-400 font-bold bg-red-950/40 px-1 rounded'
                    elif "| SUCCESS" in clean_line:
                        color = 'text-emerald-400 font-bold bg-emerald-950/40 px-1 rounded'
                    elif "| WARNING" in clean_line:
                        color = 'text-amber-400 bg-amber-950/30 px-1 rounded'
                    elif "| DEBUG" in clean_line:
                        color = 'text-gray-500'
                    else:
                        color = 'text-gray-300'

                    ui.label(clean_line).classes(f'{color} break-all font-mono tracking-tight text-[11px]')

            if new_lines:
                log_container.scroll_to(percent=1)

        except Exception as e:
            debug_box.text = f"Fallo en streaming: {e}"

    ui.timer(0.5, update_ui_logs)

    async def on_generate_report():
        try:
            report_box.set_content("⏳ *Analizando trazas en segundo plano... Por favor, espere.*")
            debug_box.text = "Extrayendo logs recientes..."

            start_time = time.time()
            log_text, metrics = build_log_report(LOG_FILE_PATH, max_lines=200)

            debug_box.text = f"Analizando {metrics['total_logs']} entradas..."

            metrics_box.text = (
                f"📋 Total Analizados: {metrics['total_logs']}  |  "
                f"🟢 INFO: {metrics['info']}  |  "
                f"⚠️ WARNINGS: {metrics['warnings']}  |  "
                f"🔴 ERRORS: {metrics['errors']}"
            )

            if not log_text:
                report_box.set_content("⚠️ **No hay suficientes datos recientes en el archivo de logs para realizar una auditoría.**")
                debug_box.text = "Log vacío"
                return

            prompt = generate_log_prompt(log_text, metrics)
            debug_box.text = "Consultando con la IA..."

            llm = LLMConnection()

            stream_generator = await run.io_bound(
                llm.ask_llama_stream,
                system_message="Eres un sistema experto en análisis de logs y auditoría DevOps. Devuelve un informe estructurado con secciones limpias, viñetas y recomendaciones claras.",
                user_message=prompt
            )

            if isinstance(stream_generator, str):
                report_box.set_content(stream_generator)
                debug_box.text = "Error en LLM"
                return

            full_report_text = ""

            def get_next_chunk(stream):
                try:
                    return next(stream)
                except StopIteration:
                    return None

            while True:
                chunk = await run.io_bound(get_next_chunk, stream_generator)
                if chunk is None:
                    break

                full_report_text += chunk['message']['content']
                report_box.set_content(full_report_text)

                await asyncio.sleep(0.01)

            elapsed = round(time.time() - start_time, 2)
            debug_box.text = f"Listo en {elapsed}s"

        except Exception as e:
            system_logger.error(f"Error en panel de administración: {e}")
            debug_box.text = f"Error crítico"
            report_box.set_content(f"💥 **ERROR EN EJECUCIÓN:**\n\n```text\n{traceback.format_exc()}\n```")