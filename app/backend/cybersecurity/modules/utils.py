from datetime import datetime

from app.backend.cybersecurity.security import SecurityManager
from app.backend.db.session import db_session


sec = SecurityManager()

def get_f_empresa(emp_id):
    """
    Función encargada de obtener el Fernet de una empreda a partir de su id mediante
    consulta a nuestras bases de datos.
    """
    with db_session(emp_id) as cur:
        cur.execute("SELECT dek_encriptada FROM empresas WHERE id = %s", (emp_id,))
        result = cur.fetchone()[0]
        return sec.get_fernet_for_empresa(result) if result else None

def cargar_empleados(empresa_id):
    """
    Función encargada de obtener el listado de empleado de una empresa dado su id mediante
    consulta a nuestras bases de datos
    """
    with db_session(empresa_id) as cur:
        cur.execute("""
            SELECT id, nombre_usuario, puesto, nombre_completo_cifrado, telefono_personal 
            FROM empleados 
            WHERE empresa_id = %s 
            ORDER BY id ASC
        """, (empresa_id,)) 
        return cur.fetchall()

def parse_stream(stream):
    """
    Función encargada de procesar la salida de un objeto generador de texto en `stream`.
    """
    for chunk in stream:
        yield chunk['message']['content']

def generate_markdown_report(text: str, nombre_empresa: str):
    """
    Función encargada de la regeneración de un informe en formato .md (MarkDown)
    """
    header = f"# AUDITORÍA DE SEGURIDAD: {nombre_empresa.upper()}\n"
    date = f"*Generado: {format_date(datetime.now())}*\n\n"
    full_content = header + date + "---\n\n" + text
    return full_content.encode('utf-8') # Simplemente devolvemos bytes utf-8


def format_date(date_dt: datetime):
    """
    Función encargada de formatear una fecha en formato `datetime` a un `string`
    """
    return date_dt.strftime("%d/%m/%Y")

def clean_name(name: str):
    """
    Función encargada de limpiar nombres para incluirlos en rutas o nombres de archivos.
    """
    return name.lower().replace(' ', '_').replace('.', '')
