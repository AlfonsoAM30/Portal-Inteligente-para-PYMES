from nicegui import ui, app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from nicegui.storage import Storage
from nicegui.persistence.pseudo_persistent_dict import PseudoPersistentDict
import sys
import os

# 1. Configuración del Path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 2. Imports locales
from app.core.logger import system_logger
from app.frontend.pages.auth_ms import auth_page
from app.frontend.pages.dashboard_ms import dashboard_page
from app.frontend.pages.admin_dashboard import admin_dashboard
from app.frontend.pages.design_ms import design_page
from app.frontend.pages.management_ms import management_page
from app.frontend.pages.recover_account import recover_account_page
from app.frontend.pages.two_factor import verify_code_page
from app.frontend.pages.password_changer import reset_password_page
import app.frontend.theme as theme


    
def check_auth(client):
    """ 
    Guardián de seguridad nativo de NiceGUI.
    Recibe el objeto 'client' (una conexión de pestaña/WebSocket activa).
    """
    path = client.page.path
    public_routes = {
        '/',
        '/login',
        '/recover-account',
        '/verify-code',
        '/reset-password'
    }
    
    if path.startswith('/_nicegui') or path.startswith('/static') or '.' in path:
        return None

    is_authenticated = app.storage.user.get('authenticated', False)

    if path not in public_routes and not is_authenticated:
        ui.navigate.to('/')
        return None
        
    if path in public_routes and is_authenticated:
        ui.navigate.to('/dashboard')
        return None
        
    return None

# Enganchamos el guardián al evento de conexión nativo
app.on_connect(check_auth)
# --- 4. DEFINICIÓN DE PÁGINAS ---
@ui.page('/')
def p_auth():
    theme.apply_global_style()
    auth_page()


@ui.page('/dashboard')
def p_dash():
    theme.apply_global_style()
    # Usamos un contenedor relativo para que el botón flote sin ocupar espacio en el flujo
    with ui.column().classes('w-full h-screen items-center justify-center m-0 p-0 overflow-hidden'):
        # Botón de cerrar sesión posicionado en la esquina superior derecha
        with ui.row().classes('absolute top-4 right-4 z-10'):
            ui.button('Cerrar Sesión', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/'))) \
                .props('flat color=red icon=logout')

        dashboard_page()


@ui.page('/design')
def p_design():
    theme.apply_global_style()
    design_page()


@ui.page('/management')
def p_manage():
    theme.apply_global_style()
    management_page()


@ui.page('/admin_dashboard')
def p_admin_dashboard():
    theme.apply_global_style()
    with ui.column().classes('w-full h-screen items-center justify-center m-0 p-0 overflow-hidden'):
        with ui.row().classes('absolute top-4 right-4 z-10'):
            ui.button('Cerrar Sesión', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/'))).props('flat color=red icon=logout')
        admin_dashboard({
            'logged': app.storage.user.get('authenticated', False),
            'rol': app.storage.user.get('rol'),
            'user_id': app.storage.user.get('user_id'),
            'empresa_id': app.storage.user.get('empresa_id'),
            'apodo': app.storage.user.get('apodo'),
            'email': app.storage.user.get('email')
        })

@ui.page('/recover-account')
def p_reset():
    theme.apply_global_style()
    recover_account_page()

@ui.page('/verify-code')
def p_verify():
    theme.apply_global_style()
    verify_code_page()

@ui.page('/reset-password')
def p_reset():
    theme.apply_global_style()
    reset_password_page()


# --- 5. EJECUCIÓN ---
if __name__ in {"__main__", "__mp_main__"}:
    Storage._create_persistent_dict = lambda id: PseudoPersistentDict()
    
    # app.add_static_files('/outputs', './app/data/output')

    ui.run(
        title='IApadrinado',
        storage_secret='clave_secreta_123',
        host="0.0.0.0",
        port=8090,
        show=False,
        reload=False,
    )