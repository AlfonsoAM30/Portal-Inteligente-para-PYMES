from nicegui import ui, app
from app.recovery_service.recovery_service import verify_recovery_code
from app.frontend.theme import Style

def verify_code_page():

    with ui.column().classes('w-full items-center mt-20 overflow-hidden'):
        ui.label('📩 Verificar código').classes('text-5xl font-bold mb-8 text-white tracking-tighter')

        with ui.column().classes('w-full max-w-md gap-4'):
            code = ui.input('Código recibido') \
                .classes('w-full') \
                .props('dark filled standout rounded')

            async def verify():
                email = app.storage.user.get("recovery_email")

                if not email:
                    ui.notify("Sesión expirada", color="negative")
                    ui.navigate.to("/")
                    return

                result = verify_recovery_code(email, code.value)

                if result.get("valid"):
                    app.storage.user["verified_recovery"] = True
                    ui.notify('Código correcto', color='positive')
                    ui.navigate.to('/reset-password')
                else:
                    ui.notify('Código incorrecto o expirado', color='negative')

            ui.button('VERIFICAR', on_click=verify).classes(f'w-full mt-4 h-12 {Style.BUTTON}')

            ui.button(
                'Volver',
                on_click=lambda: ui.navigate.to('/recover-account')
            ).props('flat color=primary')