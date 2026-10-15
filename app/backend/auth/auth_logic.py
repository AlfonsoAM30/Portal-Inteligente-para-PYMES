from app.backend.db.session import db_session
from app.backend.cybersecurity.security import SecurityManager

sec = SecurityManager()


def login_user(email, password):
    """
    Valida las credenciales contra la base de datos.
    Retorna los datos del usuario si es correcto, o un error si no.
    """
    with db_session() as cur:
        cur.execute("SELECT id, empresa_id, rol, password_hash, apodo FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()

    if not user:
        return {"error": "El correo electrónico no está registrado"}

    if not sec.check_password(password, user[3]):
        return {"error": "La contraseña es incorrecta"}

    return {
        "user_id": user[0],
        "empresa_id": user[1],
        "rol": user[2],
        "apodo": user[4],
    }


def register_company(data):
    try:
        with db_session() as cur:
            cur.execute("SELECT id FROM usuarios WHERE email = %s", (data['email'],))
            if cur.fetchone():
                return {"error": "Este correo electrónico ya está registrado"}

            _, dek_cifrada = sec.generate_new_dek()
            f_empresa = sec.get_fernet_for_empresa(dek_cifrada)

            nombre_cifrado = f_empresa.encrypt(data['nombre_real'].encode()).decode()
            password_hash = sec.hash_password(data['password'])

            cur.execute("""
                INSERT INTO empresas (nombre_empresa, dominio, telefono_oficial, dek_encriptada)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (data['nombre_empresa'], data['dominio'], data['telefono_oficial'], dek_cifrada))
            empresa_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO usuarios (empresa_id, email, nombre_completo_cifrado, apodo, password_hash, rol)
                VALUES (%s, %s, %s, %s, %s, 'user')
            """, (empresa_id, data['email'], nombre_cifrado, data['apodo'], password_hash))

        return {"success": True}
    except Exception as e:
        return {"error": f"Error en el registro: {str(e)}"}