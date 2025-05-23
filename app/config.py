import os
from dotenv import load_dotenv

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'D:/S15/dev/DB/DATABASEECDEV.FDB')
    DB_USERNAME = os.getenv('DB_USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    SESSION_DURATION = int(os.getenv('SESSION_DURATION', 5))  # Par défaut 5 minutes si non défini

    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    if ENCRYPTION_KEY:
        ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
    else:
        raise ValueError("ENCRYPTION_KEY is not set in the .env file")

    PASSWORD_SRV_MAIL = os.getenv('PASSWORD_SRV_MAIL')
