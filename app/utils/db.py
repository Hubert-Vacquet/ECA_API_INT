from fdb import connect
from app.config import Config

def get_db_connection():
    return connect(
        dsn=Config.DATABASE_PATH,
        user=Config.DB_USERNAME,
        password=Config.PASSWORD
    )
