from app.backend.db.session import db_session

def get_latest_breaches(id_empresa, limite=10):
    """
    Recupera las últimas brechas de seguridad registradas para una empresa.
    """
    try:
        with db_session(id_empresa) as cur:
            cur.execute("""
                SELECT email_afectado, tipo_brecha, riesgo, fecha 
                FROM brechas 
                WHERE empresa_id = %s 
                ORDER BY fecha DESC 
                LIMIT %s
            """, (id_empresa, limite))
            
            return cur.fetchall()
    except Exception as e:
        print(f"Error durante la recuperación de brechas del último día: {e}")
        return []

def get_breaches_last_24h(id_empresa):
    """
    Recupera solo las brechas detectadas en las últimas 24 horas para un empresa.
    """
    try:
        with db_session(id_empresa) as cur:
            cur.execute("""
                SELECT email_afectado, tipo_brecha, riesgo, fecha 
                FROM brechas 
                WHERE empresa_id = %s 
                AND fecha >= NOW() - INTERVAL '1 day'
                ORDER BY fecha DESC
            """, (id_empresa,))
            
            return cur.fetchall()
    except Exception as e:
        print(f"Error durante la recuperación de brechas del último día: {e}")
        return []