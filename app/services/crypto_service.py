from cryptography.fernet import Fernet

def encrypt_password(password: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(token: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.decrypt(token.encode()).decode()
