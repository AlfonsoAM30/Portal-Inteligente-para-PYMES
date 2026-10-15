from nicegui import ui, app
from app.recovery_service.recovery_service import send_recovery_code
from app.frontend.theme import Style

def recover_account_page():

    with ui.column().classes('w-full items-center mt-20 overflow-hidden'):
        ui.label('🔐 Recuperar cuenta').classes('text-5xl font-bold mb-8 text-white tracking-tighter')

        with ui.column().classes('w-full max-w-md gap-4'):
            email = ui.input('Introduce tu email') \
                .classes('w-full') \
                .props('dark filled standout rounded')

            async def send_code():
                if not email.value:
                    ui.notify('Introduce un email', color='warning')
                    return

                try:
                    result = send_recovery_code(email.value)

                    if result.get("exists"):
                        app.storage.user["recovery_email"] = email.value
                        ui.notify('Código enviado al correo', color='positive')
                        ui.navigate.to('/verify-code')
                    else:
                        ui.notify('El correo no existe', color='negative')

                except Exception as e:
                    ui.notify(str(e), color='negative')

            ui.button('ENVIAR CÓDIGO', on_click=send_code).classes(f'w-full mt-4 h-12 {Style.BUTTON}')

            ui.button(
                'Volver al Login',
                on_click=lambda: ui.navigate.to('/')
            ).props('flat color=primary')