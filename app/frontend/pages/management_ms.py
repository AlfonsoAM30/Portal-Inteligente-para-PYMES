import asyncio
import httpx
from nicegui import ui, app
from app.backend.db.session import db_session
from app.core.logger import system_logger
from app.backend.cybersecurity.reporter import SecurityReporter
from app.backend.services.budget_agent import analyze_budget_command

reporter = SecurityReporter()

ORCHESTRATOR_URL = "http://localhost:8000/api/orchestrator/chat"

def management_page():
    
    async def volver_al_dashboard():
        user_email = app.storage.user.get('email')
        if user_email:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        ORCHESTRATOR_URL,
                        json={
                            "thread_id": user_email,
                            "user_message": "Saliendo del panel",
                            "functional_option": "selection",
                            "reset_state": True 
                        },
                        timeout=5.0
                    )
            except Exception as e:
                system_logger.error(f"Error al resetear hilo en la salida: {e}")
                
        ui.navigate.to('/dashboard')


    async def handle_search(query: str):
        user_email = app.storage.user.get('email')
        if not user_email:
            ui.notify("Sesión expirada. Redirigiendo...", color="negative")
            ui.navigate.to('/')
            return

        if not query:
            ui.notify("Por favor, escribe algo.", color="warning")
            return

        system_logger.info(f"NiceGUI [Management]: Enviando comando con thread_id: {user_email}")

        results_area.clear()
        with results_area:
            ui.spinner(size='md')

        try:
            payload_http = {
                "thread_id": user_email,
                "management_prompt": query,
                "user_message": query,
                "functional_option": "management",
                "reset_state": False 
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(ORCHESTRATOR_URL, json=payload_http, timeout=30.0)
            
            if response.status_code != 200:
                raise Exception(f"Servidor respondió con código {response.status_code}")

            json_response = response.json()
            estado_final = json_response.get("state", {})

            payload_ui = estado_final.get("management_ui_payload") or {}
            datos = payload_ui.get("data")

            results_area.clear()
            with results_area:
                if datos is None:
                    reporte = estado_final.get("management_report", "Error: No se recibieron datos del agente de gestión.")
                    ui.label(reporte).classes('text-white')
                    return

                tipo = payload_ui.get("type")

                # --- CASO: EMPLEADOS (TABLA EDITABLE) ---
                if tipo == 'view_employees':
                    ui.label("📋 Gestión de Empleados").classes('text-2xl mb-4 text-white')
                    for emp in datos:
                        with ui.card().classes('w-full gap-4 bg-[#262626] text-white'):
                            with ui.row().classes('w-full items-center p-2'):
                                ui.number("ID", value=emp['id']).props('readonly dark').classes('w-16')
                                alias = ui.input("Alias", value=emp['alias']).props('dark')
                                puesto = ui.input("Puesto", value=emp['puesto']).props('dark')
                                nombre = ui.input("Nombre Real", value=emp['nombre']).props('dark')
                                tel = ui.input("Teléfono", value=emp['tel']).props('dark')

                                with ui.column():
                                    ui.button(icon='save', on_click=lambda e, id=emp['id']:
                                        ui.notify(f"Guardando {id}...")).props('flat color=green')

                # --- CASO: EMPRESA (FORMULARIO) ---
                elif tipo == 'view_company_data':
                    ui.label("ℹ️ Información de Empresa").classes('text-2xl mb-4 text-white')
                    with ui.row().classes('w-full gap-4'):
                        ui.input("Nombre", value=datos['nombre']).props('dark filled').classes('flex-grow')
                        ui.input("Dominio", value=datos['dominio']).props('dark filled').classes('flex-grow')
                        ui.input("Teléfono", value=datos['tel']).props('dark filled').classes('flex-grow')
                    ui.button("ACTUALIZAR INFO", on_click=lambda: ui.notify("Empresa actualizada"))

                # --- CASO: PERFIL ---
                elif tipo == 'view_personal_data':
                    ui.label("⚙️ Mi Perfil").classes('text-2xl mb-4 text-white font-bold')
                    with ui.row().classes('w-full gap-4 items-end'):
                        ui.input("Apodo", value=datos.get('apodo', '')).props('dark filled').classes('flex-grow')
                        ui.input("Email", value=datos.get('email', '')).props('dark filled readonly').classes('flex-grow')
                        ui.input("Rol", value=datos.get('rol', '')).props('dark filled readonly').classes('flex-grow')
                        ui.input("IBAN", value=datos.get('iban', '')).props('dark filled password').classes('flex-grow')
                    ui.button("GUARDAR PERFIL", on_click=lambda: ui.notify("Perfil actualizado")).classes('mt-6 bg-blue-600')

                # --- CASO: INFORME DE BRECHAS ---
                elif tipo == 'security_report':
                    ui.label("🔐 Informe de Brechas").classes('text-2xl mb-4 text-white font-bold')
                    ui.label(f"Incidentes detectados: {datos.get('breach_count', 0)}").classes('text-white mb-2')

                    breaches = datos.get('breaches', [])
                    if breaches:
                        ui.label("Detalles de brechas:").classes('text-white font-semibold mt-4 mb-2')
                        for breach in breaches:
                            with ui.card().classes('w-full gap-3 bg-[#242424] text-white mb-3'):
                                with ui.row().classes('w-full items-center p-3'):
                                    ui.label(breach['email']).classes('font-bold text-white')
                                    ui.label(f"{breach['tipo']}").classes('ml-4 text-gray-300')
                                    ui.label(f"Riesgo: {breach['riesgo']}").classes('ml-4 text-gray-300')
                                    ui.label(f"{breach['fecha']}").classes('ml-4 text-gray-300')

                        ui.label("Análisis de Seguridad (IA):").classes('text-white font-semibold mt-6 mb-2')
                        markdown_container = ui.markdown("Generando informe...").classes('text-gray-400 whitespace-pre-wrap italic')
                        
                        full_report_text = ""
                        stream_generator = reporter.generar_informe_brechas('Google', breaches, stream=True)
                        for chunk in stream_generator:
                            full_report_text += chunk['message']['content']
                            markdown_container.classes('text-white', remove='text-gray-400 italic')
                            markdown_container.set_content(full_report_text)
                            await asyncio.sleep(0.01)
                    else:
                        with ui.card().classes('w-full bg-[#1e293b] border border-emerald-500/30 p-4 mt-4 mb-3'):
                            with ui.row().classes('items-center gap-3 w-full'):
                                ui.label("🟢").classes('text-xl')
                                with ui.column().classes('gap-0'):
                                    ui.label("Estado del Sistema: Protegido").classes('text-emerald-400 font-bold text-sm uppercase tracking-wider')
                                    ui.label("Confirmación de seguridad: El sistema se encuentra íntegro y operando correctamente.").classes('text-white mt-1')

                # --- CASO: GRÁFICA DE BUDGET ---
                elif tipo == 'view_budget':
                    ui.label("💰 Gestión de Budget Inteligente").classes('text-2xl mb-4 text-white font-bold')
                    empresa_id = str(app.storage.user.get("empresa_id") or "")
                    chart_state = {'type': 'bar'}
                    if not empresa_id:
                        ui.label("❌ Error: 'empresa_id' no encontrado en la sesión.").classes("text-red-400 text-xl")
                        return

                    try:
                        with db_session(empresa_id) as cur:
                            cur.execute(
                                "SELECT total_budget, spent, api_costs, misc FROM company_budget WHERE empresa_id = %s",
                                (empresa_id,))
                            row = cur.fetchone()
                            if not row:
                                cur.execute(
                                    "INSERT INTO company_budget (empresa_id, total_budget, spent, api_costs, misc) VALUES (%s, 10000.0, 0.0, 0.0, 0.0)",
                                    (empresa_id,))
                                cur.execute(
                                    "SELECT total_budget, spent, api_costs, misc FROM company_budget WHERE empresa_id = %s",
                                    (empresa_id,))
                                row = cur.fetchone()
                        budget = {
                            "total_budget": float(row[0]),
                            "spent": float(row[1]),
                            "api_costs": float(row[2]),
                            "misc": float(row[3]),
                        }

                    except Exception as db_err:
                        ui.label(f"💥 Error de Base de Datos: {db_err}").classes("text-red-500 font-bold")
                        return

                    try:
                        chart = ui.echart(options={}).classes('w-full h-96 mt-6')
                        def refresh_chart():
                            gastos_totales = budget["spent"] + budget["api_costs"] + budget["misc"]
                            presupuesto_restante = budget["total_budget"] - gastos_totales
                            en_quiebra = presupuesto_restante < 0
                            labels = ["Presupuesto Restante", "Gastado General", "Costes API", "Otros Gastos"]
                            values = [presupuesto_restante, budget["spent"], budget["api_costs"], budget["misc"]]
                            tiene_datos = budget["total_budget"] > 0 or gastos_totales > 0
                            chart.options.clear()

                            if not tiene_datos:
                                chart.options.update({
                                    "title": {
                                        "text": "📊 No hay fondos ni gastos registrados",
                                        "subtext": "Usa la barra superior para establecer el presupuesto base",
                                        "x": "center", "y": "center",
                                        "textStyle": {"color": "#9ca3af", "fontSize": 20},
                                        "subtextStyle": {"color": "#6b7280", "fontSize": 14}
                                    },
                                    "xAxis": {"show": False}, "yAxis": {"show": False}, "series": []
                                })
                            else:
                                color_restante = "#ef4444" if en_quiebra else "#10b981"
                                colores_grafico = [color_restante, "#3b82f6", "#f59e0b", "#ec4899"]

                                if chart_state['type'] == 'bar':
                                    chart.options.update({
                                        "tooltip": {"trigger": "item", "formatter": "{b}: {c}$"},
                                        "xAxis": {"show": True, "type": "category", "data": labels},
                                        "yAxis": {"show": True, "type": "value", "scale": True},
                                        "legend": {"show": True, "top": "0%", "textStyle": {"color": "#fff"}},
                                        "series": [{
                                            "type": "bar",
                                            "data": [
                                                {"value": values[0], "itemStyle": {"color": colores_grafico[0]}},
                                                {"value": values[1], "itemStyle": {"color": colores_grafico[1]}},
                                                {"value": values[2], "itemStyle": {"color": colores_grafico[2]}},
                                                {"value": values[3], "itemStyle": {"color": colores_grafico[3]}},
                                            ],
                                            "label": {"show": True, "position": "top", "formatter": "{c}$",
                                                      "color": "#fff"}
                                        }]
                                    })

                                elif chart_state['type'] == 'pie':
                                    pie_data = []
                                    for v, l, col in zip(values, labels, colores_grafico):
                                        if v > 0 or (l == "Presupuesto Restante" and en_quiebra):
                                            pie_data.append({
                                                "value": abs(v),
                                                "name": l,
                                                "itemStyle": {"color": col},
                                                "label": {
                                                    "formatter": f"{l}: {v}$"
                                                }
                                            })

                                    chart.options.update({
                                        "xAxis": {"show": False}, "yAxis": {"show": False},
                                        "tooltip": {
                                            "trigger": "item",
                                            "formatter": "<b>{b}</b><br/>Proporción visual: {d}%"
                                        },
                                        "legend": {"show": True, "top": "0%", "left": "center",
                                                   "textStyle": {"color": "#fff"}},
                                        "series": [{
                                            "type": "pie",
                                            "radius": ["35%", "65%"], "center": ["50%", "60%"],
                                            "avoidLabelOverlap": False,
                                            "itemStyle": {"borderRadius": 10},
                                            "data": pie_data,
                                            "label": {
                                                "show": True,
                                                "color": "#fff"
                                            }
                                        }]
                                    })

                                elif chart_state['type'] == 'line':
                                    chart.options.update({
                                        "tooltip": {"trigger": "item", "formatter": "{b}: {c}$"},
                                        "xAxis": {"show": True, "type": "category", "data": labels},
                                        "yAxis": {"show": True, "type": "value", "scale": True},
                                        "legend": {"show": True, "top": "0%", "textStyle": {"color": "#fff"}},
                                        "series": [{
                                            "type": "line",
                                            "data": values,
                                            "smooth": True,
                                            "lineStyle": {"width": 4, "color": "#3b82f6"},
                                            "areaStyle": {"opacity": 0.1}
                                        }]
                                    })
                            chart.update()

                        async def procesar_comando_agentico(comando: str):

                            if not comando:
                                return
                            loading_spinner.set_visibility(True)

                            try:
                                decision = await analyze_budget_command(comando)
                                updates_made = []
                                db_updates = {}
                                if decision.total_budget is not None: db_updates["total_budget"] = decision.total_budget
                                if decision.spent is not None: db_updates["spent"] = decision.spent
                                if decision.api_costs is not None: db_updates["api_costs"] = decision.api_costs
                                if decision.misc is not None: db_updates["misc"] = decision.misc

                                valores_actuales = [budget["total_budget"], budget["spent"], budget["api_costs"],
                                                    budget["misc"]]
                                sistema_vacio = not any(v > 0 for v in valores_actuales)

                                if sistema_vacio and decision.chart_type and not db_updates:
                                    ui.notify(
                                        "❌ No hay datos disponibles. Añade datos para continuar con la solicitud.",
                                        color="warning")
                                    cmd_input.value = ""
                                    return

                                if decision.chart_type:
                                    chart_state['type'] = decision.chart_type
                                    updates_made.append(f"Visualización cambiada a {decision.chart_type}")

                                if db_updates:
                                    with db_session(empresa_id) as cur:
                                        for field, val in db_updates.items():
                                            cur.execute(
                                                f"UPDATE company_budget SET {field} = %s, updated_at = NOW() WHERE empresa_id = %s",
                                                (val, empresa_id))
                                            budget[field] = val
                                            updates_made.append(f"{field} -> {val}$")

                                if updates_made:
                                    refresh_chart()
                                    balance_final = budget["total_budget"] - (
                                                budget["spent"] + budget["api_costs"] + budget["misc"])
                                    if balance_final < 0:
                                        ui.notify(f"⚠️ ¡Alerta! Presupuesto excedido: {balance_final}$",
                                                  color="negative", close_button="Revisar")
                                    else:
                                        ui.notify(" | ".join(updates_made), color="positive", close_button="OK")
                                    cmd_input.value = ""
                                else:
                                    ui.notify("No he entendido ninguna orden clara de cambio.", color="warning")

                            except Exception as ex:
                                ui.notify(f"Error en el proceso agéntico: {ex}", color="negative")

                            finally:
                                loading_spinner.set_visibility(False)

                        with ui.row().classes('w-full items-center gap-4 mb-4'):
                            cmd_input = ui.input(
                                placeholder='Prueba con: "Añade a costes de API 12000" o "Pon presupuesto total en 50000"...'
                            ).classes('flex-grow').props('dark filled dense')
                            with cmd_input:
                                loading_spinner = ui.spinner(size='sm', color='white').classes(
                                    'self-center q-mr-sm mt-[2px]')
                                loading_spinner.set_visibility(False)
                            cmd_input.on('keydown.enter',
                                         lambda: ui.timer(0.1, lambda: procesar_comando_agentico(cmd_input.value),
                                                          once=True))
                            ui.button(icon='bolt', on_click=lambda: procesar_comando_agentico(cmd_input.value)).props(
                                'flat').classes('text-yellow-400')
                        refresh_chart()

                    except Exception as ui_err:
                        ui.label(f"💥 Error al renderizar la UI: {ui_err}").classes("text-red-500")

        except Exception as e:
            system_logger.error(f"Error de comunicación HTTP con el orquestador: {e}")
            results_area.clear()
            with results_area:
                ui.label("❌ Error de comunicación con el agente inteligente.").classes('text-red-400')

    with ui.column().classes('w-full h-screen p-10 items-center'):
        ui.button('← Volver al Dashboard', on_click=volver_al_dashboard).classes('absolute top-5 left-5 bg-transparent border border-[#48464b] text-white')

        ui.label('Management Panel').classes('text-4xl font-bold mb-8 text-white')

        with ui.row().classes('w-3/5 gap-4'):
            search_input = ui.input(placeholder='Search: empleados, clientes, perfil, brechas...').classes('flex-grow').props('dark filled')
            ui.button('SEARCH', on_click=lambda: handle_search(search_input.value)).classes('bg-[#48464b] px-6 text-white')

        results_area = ui.scroll_area().classes(
            'w-3/5 mt-10 bg-[#151515] p-8 rounded-xl border border-[#262626] h-[650px]')