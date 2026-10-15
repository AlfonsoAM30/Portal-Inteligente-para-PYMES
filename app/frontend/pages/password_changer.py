from nicegui import ui, app
from app.recovery_service.recovery_service import reset_password
from app.frontend.theme import Style

def reset_password_page():
    visible = {'pass': False, 'confirm': False}

    with ui.column().classes('w-full items-center mt-20 overflow-hidden'):

        ui.label('🔑 Nueva contraseña').classes('text-5xl font-bold mb-8 text-white tracking-tighter')

        with ui.column().classes('w-full max-w-md gap-4'):

            password = ui.input('Nueva contraseña') \
                .classes('w-full') \
                .props('dark filled standout rounded type=password')

            with password.add_slot('append'):
                eye_btn_pass = ui.button().props('flat round icon=visibility').classes('text-grey-5')
                eye_btn_pass.on('click', lambda: (
                    visible.update({'pass': not visible['pass']}),
                    password.props(f'type={"text" if visible["pass"] else "password"}'),
                    eye_btn_pass.props(f'icon={"visibility_off" if visible["pass"] else "visibility"}')
                ))

            confirm = ui.input('Confirmar contraseña') \
                .classes('w-full') \
                .props('dark filled standout rounded type=password')

            with confirm.add_slot('append'):
                eye_btn_confirm = ui.button().props('flat round icon=visibility').classes('text-grey-5')
                eye_btn_confirm.on('click', lambda: (
                    visible.update({'confirm': not visible['confirm']}),
                    confirm.props(f'type={"text" if visible["confirm"] else "password"}'),
                    eye_btn_confirm.props(f'icon={"visibility_off" if visible["confirm"] else "visibility"}')
                ))

            async def reset():
                email = app.storage.user.get("recovery_email")
                verified = app.storage.user.get("verified_recovery", False)

                if not email or not verified:
                    ui.notify("No autorizado", color="negative")
                    ui.navigate.to("/")
                    return

                if password.value != confirm.value:
                    ui.notify('Las contraseñas no coinciden', color='negative')
                    return

                result = reset_password(email, password.value)

                if result.get("updated"):
                    app.storage.user.clear()
                    ui.notify('Contraseña actualizada', color='positive')
                    ui.navigate.to('/')

            ui.button('CAMBIAR CONTRASEÑA', on_click=reset).classes(f'w-full mt-4 h-12 {Style.BUTTON}')