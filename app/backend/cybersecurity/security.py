import os
import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class SecurityManager:
    """
    Clase con todas las herramientas de seguridad utilizadas en el sistema.
    """
    def __init__(self):
        self.kek = os.getenv("KEK_MAESTRA").encode()
        self.f_master = Fernet(self.kek)

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def encrypt_data(self, data, fernet_obj):
        return fernet_obj.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data, fernet_obj):
        return fernet_obj.decrypt(encrypted_data.encode()).decode()

    def generate_new_dek(self):
        dek_plana = Fernet.generate_key()
        dek_cifrada = self.f_master.encrypt(dek_plana).decode()
        return dek_plana, dek_cifrada

    def get_fernet_for_empresa(self, dek_cifrada_db):
        dek_plana = self.f_master.decrypt(dek_cifrada_db.encode())
        return Fernet(dek_plana)