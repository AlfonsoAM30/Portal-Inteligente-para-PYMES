import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def crear_tablas_db():
    commands = [
        # 1. TABLA EMPRESAS
        """
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            nombre_empresa VARCHAR(150) NOT NULL,
            dominio VARCHAR(100) NOT NULL,
            telefono_oficial VARCHAR(20),
            dek_encriptada TEXT NOT NULL, -- La DEK cifrada por vuestra KEK
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 2. TABLA USUARIOS
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
            email VARCHAR(255) UNIQUE NOT NULL,
            nombre_completo_cifrado TEXT,
            apodo VARCHAR(50),
            telefono_cifrado TEXT,
            password_hash TEXT NOT NULL,
            rol VARCHAR(20) DEFAULT 'admin',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 3. TABLA DATOS SENSIBLES
        """
        CREATE TABLE IF NOT EXISTS datos_sensibles (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
            iban_cifrado TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 4. TABLA EMPLEADOS
        """
        CREATE TABLE IF NOT EXISTS empleados (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
            nombre_completo_cifrado TEXT,
            nombre_usuario VARCHAR(100) NOT NULL,
            puesto VARCHAR(100) NOT NULL,
            telefono_personal TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 5. TABLA BRECHAS
        """
        CREATE TABLE IF NOT EXISTS brechas (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
            email_afectado VARCHAR(100) NOT NULL,
            tipo_brecha VARCHAR(100) NOT NULL,
            riesgo VARCHAR(20) NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 6. NUEVA TABLA: CHATS (Historial de LangGraph)
        """
        CREATE TABLE IF NOT EXISTS chats (
            thread_id VARCHAR(255) PRIMARY KEY, 
            empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
            slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 3),
            
            titulo VARCHAR(150) NOT NULL DEFAULT 'Nuevo Proyecto de Diseño',
            
            product_image_url TEXT,
            product_description TEXT,
            product_reviews JSONB NOT NULL DEFAULT '[]'::jsonb,
            
            actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_empresa_slot UNIQUE (empresa_id, slot)
        )
        """,

        # --- ACTIVACIÓN DE ROW LEVEL SECURITY (RLS) ---
        "ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE datos_sensibles ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE empleados ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE brechas ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE chats ENABLE ROW LEVEL SECURITY;"

        # --- CREACIÓN DE POLÍTICAS DE SEGURIDAD ---
        # Esta política dice: "Solo puedes ver filas donde empresa_id coincida con la variable de sesión"
        """
        DO $$ 
        BEGIN
            -- (Aquí van tus políticas anteriores para usuarios, datos, empleados, brechas...)

            -- NUEVA Política para CHATS
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'p_chats_aislamiento') THEN
                CREATE POLICY p_chats_aislamiento ON chats FOR ALL 
                USING (empresa_id = CAST(current_setting('app.current_empresa_id', True) AS INTEGER));
            END IF;
        END $$;
        """
        ]

    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        print("✅ Estructura Blindada: Tablas creadas correctamente.")
    except Exception as e:
        print(f"❌ Error al configurar las tablas: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    crear_tablas_db()