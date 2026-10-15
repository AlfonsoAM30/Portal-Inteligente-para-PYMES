import httpx
from nicegui import ui, app

from app.frontend.theme import Style

MANAGEMENT_SERVICE_URL = "http://localhost:8091/api/management/auth" 

def auth_page():
    visible = {'login': False, 'reg': False}

    with ui.column().classes('w-full items-center mt-10 overflow-hidden'):
        ui.label('🤵🏻‍♂️ IApadrinado').classes('text-5xl font-bold mb-8 text-white tracking-tighter')

        with ui.tabs().classes('w-full max-w-[900px]') as tabs:
            login_tab = ui.tab('LOGIN').classes('px-10')
            reg_tab = ui.tab('REGISTER').classes('px-10')

        with ui.tab_panels(tabs, value=login_tab).classes('w-full max-w-[900px] bg-transparent'):

            # --- PANEL LOGIN ---
            with ui.tab_panel(login_tab):
                with ui.column().classes('w-full items-center py-10'):
                    with ui.column().classes('w-full max-w-md gap-4'):
                        email = ui.input('Email').classes('w-full').props('dark filled standout rounded')

                        password = ui.input('Password').classes('w-full').props('dark filled standout rounded type=password')
                        with password.add_slot('append'):
                            eye_btn_login = ui.button().props('flat round icon=visibility').classes('text-grey-5')
                            eye_btn_login.on('click', lambda: (
                                visible.update({'login': not visible['login']}),
                                password.props(f'type={"text" if visible["login"] else "password"}'),
                                eye_btn_login.props(f'icon={"visibility_off" if visible["login"] else "visibility"}')
                            ))
                        ui.button(
                            '¿Recuperar cuenta?',
                            on_click=lambda: ui.navigate.to('/recover-account')
                        ).props('flat color=primary')

                        async def handle_login():
                            if not email.value or not password.value:
                                ui.notify("Por favor, rellena todos los campos", color='warning')
                                return

                            config = {"configurable": {"thread_id": email.value}}

                            try:
                                async with httpx.AsyncClient() as client:
                                    response = await client.post(
                                        "http://localhost:8000/api/orchestrator/chat",
                                        json={
                                            "thread_id": email.value,
                                            "user_message": "Solicitud de Login desde interfaz",
                                            "functional_option": "selection",
                                            "reset_state": True,
                                            
                                            "email": email.value,
                                            "password": password.value,
                                            
                                            "design_prompt": None,
                                            "product_prompt": None,
                                            "management_prompt": None
                                        },
                                        timeout=10.0
                                    )
                                                        
                                if response.status_code != 200:
                                    ui.notify("Error de comunicación con el orquestador", color="negative")
                                    return

                                json_response = response.json()
                                estado_final = json_response.get("state", {})

                                if estado_final.get('logged'):
                                    user_data = estado_final.get('user_data', {})
                                    
                                    app.storage.user.update({
                                        'authenticated': True, 
                                        'user_id': user_data.get('user_id') or user_data.get('id'),
                                        'empresa_id': user_data.get('empresa_id'), 
                                        'apodo': user_data.get('apodo'), 
                                        'rol': user_data.get('rol'),
                                        'email': email.value
                                    })

                                    rol = user_data.get('rol')
                                    ui.notify(f'¡Hola, {user_data.get("apodo")}!', color='positive', icon='bolt')
                                    if rol == "admin":
                                        ui.navigate.to('/admin_dashboard')
                                    else:
                                        ui.navigate.to('/dashboard')
                                else:
                                    error_msg = estado_final.get("error", "Credenciales incorrectas")
                                    ui.notify(error_msg, color='negative', icon='report_problem')

                            except Exception as e:
                                ui.notify(f"Error interno del sistema: {str(e)}", color='negative')

                        ui.button('LOGIN', on_click=handle_login).classes(f'w-full mt-4 h-12 {Style.BUTTON}')

            # --- PANEL REGISTRO ---
            with ui.tab_panel(reg_tab):
                with ui.column().classes('w-full max-w-[950px] mx-auto p-6 overflow-hidden'):
                    with ui.grid(columns='1fr 1fr').classes('w-full gap-x-12 gap-y-2'):

                        with ui.row().classes('items-center gap-2 mb-2 w-full justify-center'):
                            ui.icon('business', color='cyan-5').classes('text-xl')
                            ui.label('COMPANY INFO').classes('text-xs font-bold text-cyan-500 tracking-widest')

                        with ui.row().classes('items-center gap-2 mb-2 w-full justify-center'):
                            ui.icon('verified_user', color='emerald-5').classes('text-xl')
                            ui.label('ADMIN PROFILE').classes('text-xs font-bold text-emerald-500 tracking-widest')

                        c_name = ui.input('Company Name').classes('w-full').props('dark filled standout rounded')
                        c_fullname = ui.input('Full Name').classes('w-full').props('dark filled standout rounded')
                        c_domain = ui.input('Domain').classes('w-full').props('dark filled standout rounded')
                        c_apodo = ui.input('Nickname').classes('w-full').props('dark filled standout rounded')
                        c_phone = ui.input('Official Phone').classes('w-full').props('dark filled standout rounded')
                        c_email = ui.input('Admin Email').classes('w-full').props('dark filled standout rounded')

                        ui.label('')

                        c_pass = ui.input('Password').classes('w-full').props('dark filled standout rounded type=password')
                        with c_pass.add_slot('append'):
                            eye_btn_reg = ui.button().props('flat round icon=visibility').classes('text-grey-5')
                            eye_btn_reg.on('click', lambda: (
                                visible.update({'reg': not visible['reg']}),
                                c_pass.props(f'type={"text" if visible["reg"] else "password"}'),
                                eye_btn_reg.props(f'icon={"visibility_off" if visible["reg"] else "visibility"}')
                            ))

                    with ui.row().classes('w-full justify-center mt-10'):
                        async def handle_reg():
                            fields = {
                                'Company Name': c_name.value, 'Domain': c_domain.value, 'Phone': c_phone.value,
                                'Full Name': c_fullname.value, 'Nickname': c_apodo.value,
                                'Email': c_email.value, 'Password': c_pass.value
                            }
                            if not all(fields.values()):
                                ui.notify("Por favor, rellena todos los campos", color='warning', position='top')
                                return

                            payload_reg = {
                                'nombre_empresa': c_name.value, 
                                'dominio': c_domain.value,
                                'telefono_oficial': c_phone.value,
                                'nombre_real': c_fullname.value, 
                                'email': c_email.value, 
                                'apodo': c_apodo.value,
                                'password': c_pass.value
                            }

                            try:
                                async with httpx.AsyncClient() as client:
                                    response = await client.post(
                                        f"{MANAGEMENT_SERVICE_URL}/register", 
                                        json=payload_reg,
                                        timeout=5.0
                                    )
                                
                                if response.status_code in [200]:
                                    ui.notify("Registro corporativo exitoso", color='positive', icon='check')
                                    tabs.set_value(login_tab)
                                else:
                                    error_detail = response.json().get("detail", "Error al registrar la empresa")
                                    ui.notify(error_detail, color='negative')
                            except Exception as e:
                                ui.notify(f"Error de conexión con el servicio de registro: {str(e)}", color='negative')

                        ui.button('CREATE COMPANY ACCOUNT', on_click=handle_reg).classes(
                            f'w-80 h-14 text-lg font-bold {Style.BUTTON}')