import httpx
from nicegui import ui, app
from app.core.logger import system_logger

ORCHESTRATOR_URL = "http://localhost:8000/api/orchestrator/chat"
MANAGEMENT_SERVICE_URL = "http://localhost:8091/api/management"
PLACEHOLDER_IMG = "https://via.placeholder.com/300?text=Producto"

def design_page():
    user_email = app.storage.user.get('email')
    empresa_id = app.storage.user.get('empresa_id')

    if not app.storage.user.get('thread_id_actual'):
        app.storage.user['thread_id_actual'] = user_email
        
    system_logger.info(f"🎨 Frontend: Lienzo temporal activado para {user_email}")
    ui.add_head_html('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600&display=swap');
            
            body { 
                overflow: hidden; 
                margin: 0; 
                padding: 0; 
                font-family: 'Inter', sans-serif; 
                background-color: #0d0d0d;
            }
            
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: #555; }

            .main-container {
                height: 100vh;
                width: 100vw;
            }
            
            .container-card { 
                background: linear-gradient(145deg, #161616, #121212);
                border: 1px solid rgba(255, 255, 255, 0.06); 
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                border-radius: 16px; 
                padding: 20px;
                display: flex;
                flex-direction: column;
                width: 100%;
            }
            
            .image-frame {
                background-color: white !important;
                border-radius: 8px;
                aspect-ratio: 1 / 1; 
                width: 30%; 
                margin: 0 auto;      
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
                flex-shrink: 0;
                padding: 10px; 
            }
            
            .force-contain img {
                object-fit: contain !important;
                transition: opacity 0.3s ease;
            }
            
            .message-text {
                word-break: break-word;
                line-height: 1.5;
            }
            .chat-msg-width {
                max-width: 85%;
            }
            
            .input-wrapper {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
            }
            .input-wrapper:focus-within {
                border-color: rgba(255, 255, 255, 0.2);
            }
        </style>
    ''')

    # --- Lógica de Navegación ---
    async def volver_al_dashboard():
        user_email = app.storage.user.get('email')
        if user_email:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        ORCHESTRATOR_URL,
                        json={
                            "thread_id": user_email,
                            "user_message": "Saliendo del estudio de diseño",
                            "functional_option": "selection",
                            "reset_state": True  
                        },
                        timeout=5.0
                    )
            except Exception as e:
                system_logger.error(f"Error al resetear hilo de diseño: {e}")
        ui.navigate.to('/dashboard')

    with ui.left_drawer(top_corner=True, bottom_corner=True) \
            .props('width=240 behavior=desktop') \
            .classes('bg-[#111111] border-r border-[#262626] text-white p-4') as sidebar:
        ui.label('🎨 Mis Proyectos (Máx 3)').classes('text-xs font-bold text-cyan-400 mb-4 tracking-wider text-center block uppercase')
        botones_container = ui.column().classes('w-full gap-2')
        ui.button('➕ Lienzo Temporal Nuevo', on_click=lambda: activar_lienzo_temporal()).classes(
            'w-full mt-6 bg-cyan-600 hover:bg-cyan-700 text-[10px] font-bold h-9 rounded-lg transition-all'
        )

    async def refrescar_sidebar():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{MANAGEMENT_SERVICE_URL}/chats/{empresa_id}")
                if response.status_code == 200:
                    chats_activos = response.json()
                    botones_container.clear()
                    
                    with botones_container:
                        if not chats_activos:
                            ui.label('No hay proyectos guardados.').classes('text-gray-500 text-xs italic p-2')
                        
                        for chat in chats_activos:
                            def crear_click_handler(
                                slot_thread_id=chat['thread_id'], 
                                img_url=chat['product_image_url'], 
                                tit=chat['titulo'],
                                desc_db=chat.get('product_description'),
                                reviews_db=chat.get('product_reviews')
                            ):
                                async def cargar_proyecto_guardado():
                                    app.storage.user['thread_id_actual'] = slot_thread_id
                                    ui.notify(f"Cargando Proyecto: {tit}", color="info")
                                    
                                    img_display.set_source(img_url or PLACEHOLDER_IMG)
                                    title_display.set_text(tit)
                                    desc_display.set_text(desc_db)
                                    btn_guardar.set_visibility(False)
                                    
                                    reviews_container.clear()
                                    if reviews_db:
                                        for r in reviews_db:
                                            with reviews_container:
                                                ui.label(f'"{r}"').classes('text-gray-300 text-xs italic border-l-2 border-white/10 pl-2 py-1')
                                    else:
                                        with reviews_container:
                                            ui.label('No se encontraron reseñas guardadas.').classes('text-gray-500 text-xs italic')
                                    
                                    messages_column.clear()
                                    
                                    try:
                                        app.storage.user['product_prompt'] = chat.get('product_prompt') or img_url

                                        async with httpx.AsyncClient() as orchestrator_client:
                                            res_state = await orchestrator_client.post(ORCHESTRATOR_URL, json={
                                                "thread_id": slot_thread_id,
                                                "user_message": "Cargando estado del proyecto", 
                                                "product_prompt": chat.get('product_prompt') or img_url,
                                                "product_title": tit,
                                                "product_description": desc_db,
                                                "product_image_url": img_url,
                                                "functional_option": "design",
                                                "user_intention": "wait",
                                                "reset_state": False,
                                            })
                                            
                                            if res_state.status_code == 200:
                                                state_data = res_state.json().get("state", {})
                                                historial_mensajes = state_data.get('messages', [])
                                                
                                                if historial_mensajes:
                                                    for msg in historial_mensajes:
                                                        if not isinstance(msg, dict): continue
                                                        
                                                        content = msg.get('content', '').strip()
                                                        type_msg = msg.get('type', '').lower()
                                                        
                                                        if not content or type_msg == 'system' or "Cargando estado" in content: 
                                                            continue
                                                            
                                                        if type_msg == 'human':
                                                            with messages_column:
                                                                ui.chat_message(content, sent=True).classes(
                                                                    'chat-msg-width self-end message-text'
                                                                ).props('bg-color=primary text-color=white')
                                                                
                                                        elif type_msg in ['ai', 'assistant']:
                                                            with messages_column:
                                                                ui.chat_message(content, sent=False).classes(
                                                                    'chat-msg-width message-text'
                                                                ).props('bg-color=grey-9 text-color=white')
                                                else:
                                                    with messages_column:
                                                        ui.chat_message(f"Proyecto '{tit}' cargado. Escribe un mensaje para empezar a diseñar.", sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')
                                            else:
                                                ui.notify("⚠️ No se pudo recuperar el chat desde el Orquestador.", color="warning")
                                    except Exception as e:
                                        system_logger.error(f"Error recuperando mensajes de LangGraph: {e}")
                                        with messages_column:
                                            ui.chat_message("Error al sincronizar el histórico de conversación.", sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')
                                    
                                    chat_box.scroll_to(percent=1)
                                return cargar_proyecto_guardado

                            ui.button(
                                f"📦 Slot {chat['slot']}: {chat['titulo'][:18]}...", 
                                on_click=crear_click_handler()
                            ).classes('w-full text-left justify-start bg-transparent border border-white/5 hover:bg-white/5 text-gray-300 text-xs h-10 truncate rounded-md')

        except Exception as e:
            system_logger.error(f"Error cargando sidebar: {e}")

    def activar_lienzo_temporal():
        app.storage.user['thread_id_actual'] = app.storage.user.get('email')
        img_display.set_source(PLACEHOLDER_IMG)
        title_display.set_text('Esperando producto...')
        desc_display.set_text('Sube una URL para ver los detalles del producto.')
        messages_column.clear()
        with messages_column:
            ui.chat_message("Hola. Pega la URL de un producto para empezar a diseñar.", sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')
        btn_guardar.set_visibility(False)
        ui.notify("Mesa de trabajo limpia (Canal Temporal)", color="primary")


    with ui.row().classes('main-container p-6 no-wrap gap-6 items-stretch'):

        # --- COLUMNA IZQUIERDA ---
        with ui.column().classes('flex-1 basis-1/2 gap-4 h-full no-wrap'):
            
            # Bloque de la Imagen del Producto
            with ui.column().classes('container-card flex-none justify-center items-center py-8 relative'):
                ui.button('← Dashboard', on_click=volver_al_dashboard).classes('absolute top-4 left-4 bg-transparent border border-white/10 text-white text-xs')
                
                with ui.element('div').classes('image-frame mt-4'):
                    img_display = ui.image(PLACEHOLDER_IMG) \
                        .style('width: 100%; height: 100%; object-fit: contain;') \
                        .classes('force-contain')

                title_display = ui.label('Esperando producto...').classes(
                    'text-gray-200 text-lg font-semibold mt-6 text-center tracking-wide')

                btn_guardar = ui.button('💾 Guardar Proyecto').classes(
                    'mt-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors'
                )
                btn_guardar.set_visibility(False)
                
                async def guardar_en_slot_libre():
                    empresa_id = app.storage.user.get('empresa_id')
                    user_email = app.storage.user.get('email')
                    
                    try:
                        async with httpx.AsyncClient() as client:
                            res_get = await client.get(f"{MANAGEMENT_SERVICE_URL}/chats/{empresa_id}")
                            if res_get.status_code != 200:
                                ui.notify("No se pudo cargar el estado de los slots.", color="negative")
                                return
                            chats_activos = res_get.json()
                            slots_ocupados = {c['slot'] for c in chats_activos}
                            slot_libre = next((s for s in [1, 2, 3] if s not in slots_ocupados), None)
                            if slot_libre is None:
                                ui.notify("❌ Límite alcanzado: Ya tienes 3 proyectos guardados. Elimina uno primero.", color="negative")
                                return
                            nuevo_thread_id = f"{user_email}_slot_{slot_libre}"
                            titulo_actual = title_display.text if title_display.text != 'Esperando producto...' else 'Proyecto sin título'
                            descripcion_actual = desc_display.text
                            reviews_actuales = app.storage.user.get('product_reviews_cache') or []
                            
                            res_save = await client.post(
                                f"{MANAGEMENT_SERVICE_URL}/chats/save",
                                json={
                                    "thread_id": nuevo_thread_id,
                                    "empresa_id": int(empresa_id),
                                    "slot": slot_libre,
                                    "titulo": titulo_actual,
                                    "product_image_url": img_display.source,
                                    "product_description": descripcion_actual,
                                    "product_reviews": reviews_actuales
                                }
                            )
                            if res_save.status_code != 200:
                                try:
                                    error_msg = res_save.json().get("detail")
                                except Exception:
                                    error_msg = res_save.text
                                ui.notify(f"Error al guardar: {error_msg}", color="negative")
                                return
                            
                            await client.post(
                                ORCHESTRATOR_URL,
                                json={
                                    "thread_id": nuevo_thread_id,
                                    "user_message": "Guardando...",
                                    "functional_option": "design",
                                    "user_intention": "wait",
                                    "reset_state": False,
                                    "product_prompt": app.storage.user.get('product_prompt'),
                                    "product_image_url": img_display.source,
                                    "product_description": descripcion_actual,
                                    "product_reviews": reviews_actuales,
                                    "design_prompt": "Sincronización de guardado"
                                }
                            )
                            
                            ui.notify(f"💾 ¡Proyecto guardado con éxito en el Slot {slot_libre}!", color="positive", icon="cloud_done")
                            btn_guardar.set_visibility(False)
                            
                            try:
                                await refrescar_sidebar()
                            except Exception as e:
                                system_logger.error(f"Error refrescando barra lateral tras guardar: {e}")
                            
                    except Exception as e:
                        system_logger.error(f"Error al guardar proyecto: {e}")
                        ui.notify(f"Error inesperado al guardar: {e}", color="negative")

                btn_guardar.on('click', guardar_en_slot_libre)

            with ui.row().classes('w-full flex-grow gap-4 no-wrap'): 
                with ui.column().classes('container-card flex-1 h-full'):
                    ui.label('INFORMACIÓN').classes('text-gray-500 text-[10px] font-bold tracking-widest mb-2 uppercase')
                    with ui.scroll_area().classes('flex-grow w-full pr-2'):
                        desc_display = ui.label('Sube una URL para ver los detalles del producto.').classes('text-gray-300 text-sm font-light leading-relaxed')

                with ui.column().classes('container-card flex-1 h-full'):
                    ui.label('RESEÑAS DESTACADAS').classes('text-gray-500 text-[10px] font-bold tracking-widest mb-2 uppercase')
                    with ui.scroll_area().classes('flex-grow w-full pr-2'):
                        reviews_container = ui.column().classes('w-full gap-3')
                        with reviews_container:
                            ui.label('Aún no hay datos.').classes('text-gray-600 text-sm italic')

        # --- COLUMNA DERECHA (CHAT) ---
        with ui.column().classes('flex-1 basis-1/2 container-card h-full no-wrap relative'):
            with ui.row().classes('w-full items-center justify-between mb-4'):
                
                with ui.row().classes('items-center gap-2'):
                    ui.button(on_click=lambda: sidebar.toggle()) \
                        .props('flat round dense icon=menu').classes('text-gray-400 hover:text-white')
                    ui.label('Design Studio AI').classes('text-white text-xl font-semibold tracking-wide')
                
                ui.icon('auto_awesome', color='gray-400').classes('text-xl')

            chat_box = ui.scroll_area().classes('flex-grow w-full border-t border-white/5 pt-4 pb-20') 
            with chat_box:
                messages_column = ui.column().classes('w-full gap-3 p-2')
                with messages_column:
                    ui.chat_message("Hola. Pega la URL de un producto para empezar a diseñar.", sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')

            with ui.column().classes('absolute bottom-4 left-4 right-4 bg-[#121212] pt-2'):
                status_area = ui.row().classes('w-full px-2 h-6 items-center')

                with ui.row().classes('w-full items-center input-wrapper rounded-full px-4 py-1 mt-1 transition-all'):
                    input_field = ui.input(placeholder='Instruye a la IA o pega una URL...') \
                        .props('dark borderless').classes('flex-grow text-white text-sm') \
                        .on('keydown.enter', lambda: handle_send())
                    ui.button(on_click=lambda: handle_send()).props('flat round dense icon=arrow_upward').classes('text-white bg-white/10 hover:bg-white/20 transition-colors ml-2')


    async def handle_send():
        text = input_field.value.strip()
        if not text: return
        input_field.value = ''

        user_email = app.storage.user.get('email')
        if not user_email: return
        
        thread_id_para_orquestador = app.storage.user.get('thread_id_actual') or user_email
        product_loaded = img_display.source != PLACEHOLDER_IMG

        with messages_column:
            ui.chat_message(text, sent=True).classes('chat-msg-width self-end message-text').props('bg-color=primary text-color=white') 
        chat_box.scroll_to(percent=1)

        try:
            if not product_loaded:
                if not text.startswith('http'):
                    ui.notify("Por favor, pega primero la URL del producto.", color="warning")
                    return
                
                with status_area:
                    ui.spinner('dots', size='sm', color='gray-400')
                    ui.label('Extrayendo datos de la tienda...').classes('ml-2 text-gray-400 text-xs tracking-wide')

                payload_http = {
                    "thread_id": thread_id_para_orquestador,
                    "user_message": text,
                    "product_prompt": text,
                    "design_prompt": text,
                    "functional_option": "design",
                    "reset_state": True
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(ORCHESTRATOR_URL, json=payload_http, timeout=45.0)

                if response.status_code != 200:
                    raise Exception(f"Error en orquestador: {response.status_code}")

                json_res = response.json()
                estado_final = json_res.get("state", {})
                
                img_display.set_source(estado_final.get('product_image_url') or PLACEHOLDER_IMG)
                title_display.set_text(estado_final.get('product_title') or 'Producto Listo')
                desc_display.set_text(estado_final.get('product_description') or 'Sin descripción disponible.')
                
                btn_guardar.set_visibility(True)
                app.storage.user['product_prompt'] = text
                
                reviews_actuales = estado_final.get('product_reviews') or []
                app.storage.user['product_reviews_cache'] = reviews_actuales

                reviews_container.clear()
                if reviews_actuales:
                    for r in reviews_actuales:
                        with reviews_container:
                            ui.label(f'"{r}"').classes('text-gray-300 text-xs italic border-l-2 border-white/10 pl-2 py-1')
                else:
                    with reviews_container:
                        ui.label('No se encontraron reseñas para este producto.').classes('text-gray-500 text-xs italic')
                
                with messages_column:
                    ui.chat_message("Producto analizado correctamente. ¿Qué diseño o análisis quieres que haga?", sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')

            else:
                if text.startswith('http'):
                    ui.notify("Ya tienes un producto cargado. ¡Pídeme un diseño!", color="info")
                    return

                with status_area:
                    ui.spinner('puff', size='sm', color='accent')
                    ui.label('Generando arte...').classes('ml-2 text-gray-400 text-xs tracking-wide')
                
                try:
                    payload_http = {
                        "thread_id": thread_id_para_orquestador,
                        "user_message": text,
                        "design_prompt": text,
                        "functional_option": "design",
                        "reset_state": False
                    }

                    async with httpx.AsyncClient() as client:
                        response = await client.post(ORCHESTRATOR_URL, json=payload_http, timeout=60.0)

                    if response.status_code != 200:
                        raise Exception(f"Error del servidor de IA: {response.status_code}")

                    json_res = response.json()
                    estado_final = json_res.get("state", {})
                    user_intention = estado_final.get('user_intention')

                    if user_intention == 'new_enviroment':
                        new_img_url = estado_final.get('generated_img_url')
                        if new_img_url:
                            img_display.set_source(new_img_url)
                            ui.notify("¡Imagen de ambiente generada con éxito!", color="positive")
                        else:
                            img_display.set_source(estado_final.get('product_image_url') or PLACEHOLDER_IMG)
                        reply = estado_final.get('assistant_response') or 'El entorno publicitario ha sido completado.'
                    
                    elif user_intention == 'analysis':
                        reply = estado_final.get('assistant_response') or 'Análisis de mercadotecnia completado.'
                        ui.notify("Se ha analizado tu propuesta comercial", color="positive")
                    
                    else:
                        reply = estado_final.get('assistant_response') or "He procesado tu petición con éxito."
                    
                    with messages_column:
                        ui.chat_message(reply, sent=False).classes('chat-msg-width message-text').props('bg-color=grey-9 text-color=white')
                            
                except Exception as e:
                    system_logger.error(f"Error en generación creativa: {e}")
                    ui.notify("Error al procesar el prompt de generación", color="negative")

        except Exception as e:
            system_logger.error(f"Error general en flujo de diseño: {e}")
            ui.notify("Error de comunicación con el agente de diseño.", color="negative")
        
        status_area.clear()
        chat_box.scroll_to(percent=1)

    ui.timer(0.2, refrescar_sidebar, once=True)