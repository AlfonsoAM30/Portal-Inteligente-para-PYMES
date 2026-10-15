from nicegui import ui, app

def dashboard_page():
    """
    Hub Principal de Selección.
    Navegación web pura y limpia. Guarda la elección en la sesión del navegador
    para que la pantalla de destino sepa qué contexto inyectar en el chat.
    """
    
    def handle_selection(opcion: str, ruta_web: str):
        app.storage.user.update({'active_branch': opcion})
        
        ui.navigate.to(ruta_web)

    with ui.column().classes('w-full items-center justify-center gap-6 mt-16'):
        ui.label('Selecciona padrino a utilizar').classes('text-4xl font-bold mb-10 text-white tracking-tight')

        with ui.row().classes('gap-10 justify-center items-center w-full max-w-xl'):
            
            # --- BOTÓN DISEÑO ---
            with ui.button(on_click=lambda: handle_selection('design', '/design')) \
                    .classes('w-64 h-36 text-xl font-bold bg-[#1f1f1f] hover:bg-[#333236] text-white border border-stone-800 rounded-xl transition-all shadow-md flex-col gap-2'):
                ui.icon('palette', size='md').classes('text-purple-400')
                ui.label('DISEÑO CREATIVO').classes('tracking-wide text-sm')

            # --- BOTÓN GESTIÓN ---
            with ui.button(on_click=lambda: handle_selection('management', '/management')) \
                    .classes('w-64 h-36 text-xl font-bold bg-[#1f1f1f] hover:bg-[#333236] text-white border border-stone-800 rounded-xl transition-all shadow-md flex-col gap-2'):
                ui.icon('shield', size='md').classes('text-cyan-400')
                ui.label('GESTIÓN CORPORATIVA').classes('tracking-wide text-sm')