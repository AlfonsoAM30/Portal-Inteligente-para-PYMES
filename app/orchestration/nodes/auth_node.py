import httpx
from app.orchestration.state import State
from app.core.logger import system_logger

# Configuración del microservicio comercial (puerto 8091)
MANAGEMENT_SERVICE_URL = "http://localhost:8091/api/management/auth"

async def auth_node(state: State) -> dict:
    """
    Nodo Soberano de Autenticación.
    Recibe el email y password del estado inicial, ataca al microservicio
    comercial y guarda la sesión directamente en Postgres de por vida.
    """
    auth_req = state.get("auth_credentials") or {}
    email = auth_req.get("email")
    password = auth_req.get("password")

    if not email or not password:
        system_logger.info("🔑 Auth Node: Reanudación detectada. Sesión ya persistida en Postgres.")
        return {}

    system_logger.info(f"🔑 Auth Node: Solicitando Login al MS comercial para: {email}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MANAGEMENT_SERVICE_URL}/login",
                json={"email": email, "password": password},
                timeout=5.0
            )
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get("user", {})
            empresa_id = user_data.get("empresa_id")

            system_logger.success(f"🔑 Auth Node: Login correcto. Empresa ID [{empresa_id}] fijada en Postgres.")
            
            return {
                "logged": True,
                "user_data": user_data,
                "auth_credentials": {
                    "email": email,
                    "empresa_id": str(empresa_id) if empresa_id else None
                },
            }
        else:
            error_detail = response.json().get("detail", "Credenciales incorrectas")
            system_logger.warning(f"❌ Auth Node: Denegado -> {error_detail}")
            return {
                "logged": False,
                "error": error_detail
            }

    except Exception as e:
        system_logger.error(f"💥 Auth Node: Error al conectar con el servicio: {str(e)}")
        return {
            "logged": False,
            "error": "Error de conexión con el servidor de autenticación."
        }