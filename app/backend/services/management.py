import os
from cryptography.fernet import Fernet

from app.backend.db.session import db_session
from app.backend.cybersecurity.reporter import SecurityReporter

reportero = SecurityReporter()

def get_decryption_tool(cur, empresa_id):
    """
    Obtiene la DEK de la empresa, la desencripta con la KEK
    y devuelve un objeto Fernet listo para usar.
    """
    cur.execute("SELECT dek_encriptada FROM empresas WHERE id = %s", (empresa_id,))
    dek_cifrada = cur.fetchone()[0]

    kek = Fernet(os.getenv("KEK_MAESTRA"))  # Asegúrate de tener esto en tu .env
    dek_limpia = kek.decrypt(dek_cifrada.encode()).decode()

    return Fernet(dek_limpia)


def load_employes(id):
    with db_session(id) as cur:
        f = get_decryption_tool(cur, id)

        cur.execute("""
            SELECT id, nombre_usuario, puesto, nombre_completo_cifrado, telefono_personal 
            FROM empleados WHERE empresa_id = %s ORDER BY id ASC
        """, (id,))
        rows = cur.fetchall()

        result = []
        for row in rows:
            nombre = f.decrypt(row[3].encode()).decode()
            telefono = f.decrypt(row[4].encode()).decode()
            result.append((row[0], row[1], row[2], nombre, telefono))
        return result


def view_personal_data(empresa_id):
    with db_session(empresa_id) as cur:
        f = get_decryption_tool(cur, empresa_id)

        cur.execute("""
            SELECT 
                u.id, u.email, u.apodo, u.rol, d.iban_cifrado, u.fecha
            FROM usuarios u
            LEFT JOIN datos_sensibles d 
                ON u.id = d.usuario_id
            WHERE u.empresa_id = %s
        """, (empresa_id,))

        rows = cur.fetchall()

        result = []
        for row in rows:

            if row[4]:
                try:
                    iban = f.decrypt(row[4].encode()).decode()
                except Exception:
                    iban = "Error descifrando"
            else:
                iban = "No asignado"

            result.append((
                row[0], row[1], row[2], row[3], iban, row[5]
            ))

        return result


def view_company_data(empresa_id):
    with db_session(empresa_id) as cur:
        cur.execute("""
            SELECT id, nombre_empresa, dominio, telefono_oficial, fecha 
            FROM empresas WHERE id = %s
        """, (empresa_id,))
        return cur.fetchone()


def security_report(empresa_id):
    with db_session(empresa_id) as cur:
        cur.execute("SELECT nombre_empresa FROM empresas WHERE id = %s", (empresa_id,))
        empresa_row = cur.fetchone()
        nombre_empresa = empresa_row[0] if empresa_row else 'Empresa'

        cur.execute("""
            SELECT email_afectado, tipo_brecha, riesgo, fecha 
            FROM brechas WHERE empresa_id = %s ORDER BY riesgo DESC
        """, (empresa_id,))
        rows = cur.fetchall()

    data = [
        {"email": r[0], "tipo": r[1], "riesgo": r[2], "fecha": r[3]}
        for r in rows
    ]

    """if rows:
        informe = reportero.generar_informe_brechas(nombre_empresa, rows)
    else:
        informe = "No se detectaron brechas en la empresa."""

    return {
        "breach_count": len(rows),
        "breaches": data
    }