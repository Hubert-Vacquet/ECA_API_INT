import os
import hashlib
from datetime import datetime, timedelta
from app.utils.db import get_db_connection
from app.config import Config
import uuid


def generate_session_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()

def is_session_valid(uid, token):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT DATE_HEURE_FIN
            FROM SESSION_UTILISATEUR
            WHERE UID = ? AND TOKEN = ?
        """, (uid, token))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result is None:
            return False  # Aucune session trouvée

        date_fin = result[0]
        if date_fin is None:
            return False  # La session n’a pas de date de fin → invalide

        return datetime.now() < date_fin  # True si pas expirée

    except Exception as e:
        print(f"[ERREUR] is_session_valid: {e}")
        return False


def create_user_session(uid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        token = str(uuid.uuid4())  # Génère un token unique
        date_debut = datetime.now()
        date_fin = date_debut + timedelta(minutes=int(Config.SESSION_DURATION))

        cur.execute("""
            INSERT INTO SESSION_UTILISATEUR (UID, DATE_HEURE_DEBUT, DATE_HEURE_FIN, TOKEN)
            VALUES (?, ?, ?, ?)
        """, (uid, date_debut, date_fin, token))

        conn.commit()
        cur.close()
        conn.close()

        return token  # On retourne le token au client

    except Exception as e:
        print(f"[ERREUR] create_user_session: {e}")
        return None


def clean_expired_sessions():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM SESSION_UTILISATEUR
            WHERE DATE_HEURE_FIN < ?
        """, (datetime.now(),))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Sessions expirées supprimées.")
        return True
    except Exception as e:
        print(f"[ERREUR] Nettoyage des sessions : {e}")
        return False
