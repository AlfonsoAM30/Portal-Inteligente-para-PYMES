import os
import psycopg2
from contextlib import contextmanager


@contextmanager
def db_session(empresa_id=None):
    """
    Función encargada de realizar conexión con nuestra base de datos.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    try:
        if empresa_id:
            cur.execute(f"SET app.current_empresa_id = '{empresa_id}';")
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()