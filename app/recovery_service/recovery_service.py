import os
import random
import time
from dotenv import load_dotenv

from app.backend.cybersecurity.security import SecurityManager
from app.backend.db.session import db_session  # tu context manager psycopg2
from app.core.send_email import send_email

load_dotenv()

def send_recovery_code(email: str):
    """
    1. Verifica si el email existe en DB
    2. Genera código OTP
    3. Lo guarda en DB (NO RAM)
    4. Lo envía por email
    """

    with db_session() as cur:
        cur.execute(
            "SELECT id FROM usuarios WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()

        if not user:
            return {"exists": False}
        
        code = str(random.randint(100000, 999999))
        expires_at = int(time.time()) + 300

        cur.execute("""
            CREATE TABLE IF NOT EXISTS recovery_codes (
                email TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                expires_at BIGINT NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO recovery_codes (email, code, expires_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (email)
            DO UPDATE SET code = EXCLUDED.code,
                          expires_at = EXCLUDED.expires_at
        """, (email, code, expires_at))

        send_email(
            to_email=email,
            subject="Código de recuperación",
            body=f"Tu código es: {code}"
        )

        return {"exists": True}


def verify_recovery_code(email: str, code: str):

    with db_session() as cur:

        cur.execute("""
            SELECT code, expires_at
            FROM recovery_codes
            WHERE email = %s
        """, (email,))

        row = cur.fetchone()

        if not row:
            return {"valid": False}

        stored_code, expires_at = row
        if int(time.time()) > expires_at:
            return {"valid": False}
        if stored_code != code:
            return {"valid": False}

        return {"valid": True}


def reset_password(email: str, new_password: str):

    with db_session() as cur:
        cur.execute(
            "SELECT id FROM usuarios WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()

        if not user:
            return {"updated": False}
        security = SecurityManager()
        hashed_password = security.hash_password(new_password)

        cur.execute("""
            UPDATE usuarios
            SET password_hash = %s
            WHERE email = %s
        """, (hashed_password, email))

        cur.execute("""
            DELETE FROM recovery_codes
            WHERE email = %s
        """, (email,))

        return {"updated": True}