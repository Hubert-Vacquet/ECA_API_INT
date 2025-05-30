from cryptography.fernet import Fernet

def encrypt_password(password: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(token: str, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.decrypt(token.encode()).decode()

def check_password(plain_password: str, encrypted_password: str, key: bytes) -> bool:
    try:
        decrypted_password = decrypt_password(encrypted_password, key)
        return plain_password == decrypted_password
    except Exception:
        return False
