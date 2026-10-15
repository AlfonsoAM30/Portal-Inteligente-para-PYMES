from nicegui import ui


def apply_global_style():
    # Fondo oscuro y fuente global
    ui.query('body').style('margin: 0; padding: 0; overflow: hidden;')
    ui.query('body').style('background-color: rgba(0, 0, 0, 0.85); color: white; font-family: Arial, sans-serif;')

    # Inyectar estilos CSS para componentes de NiceGUI (Quasar)
    ui.add_head_html('''
        <style>
            .q-field--filled .q-field__control { background: #1f1f1f !important; }
            .q-field__native, .q-field__input { color: white !important; }
            .q-field__label { color: #888 !important; }
        </style>
    ''')


class Style:
    BUTTON = 'bg-[#48464b] text-white font-bold rounded-lg px-6 py-2'
    CARD = 'bg-[#151515] border border-[#262626] rounded-xl p-6'