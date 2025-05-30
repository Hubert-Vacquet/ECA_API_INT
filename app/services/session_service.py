from datetime import datetime, timedelta
from app.utils.db import get_db_connection
from app.config import Config
import uuid


def create_or_update_session(uid):
    """
    Crée ou met à jour une session pour un utilisateur donné.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    token = str(uuid.uuid4())
    now = datetime.now()
    expiration = now + timedelta(minutes=Config.SESSION_DURATION)
    print(f"[create_or_update_session] Nouveau token pour UID {uid} : {token}, expire à {expiration}")
    cursor.execute("""
        SELECT COUNT(*) FROM SESSION_UTILISATEUR WHERE UID = ?
    """, (uid,))
    exists = cursor.fetchone()[0]

    if exists:
        cursor.execute("""
            UPDATE SESSION_UTILISATEUR
            SET TOKEN = ?, DATE_HEURE_DEBUT = ?, DATE_HEURE_FIN = ?
            WHERE UID = ?
        """, (token, now, expiration, uid))
    else:
        cursor.execute("""
            INSERT INTO SESSION_UTILISATEUR (UID, TOKEN, DATE_HEURE_DEBUT, DATE_HEURE_FIN)
            VALUES (?, ?, ?, ?)
        """, (uid, token, now, expiration))

    conn.commit()
    cursor.close()
    conn.close()

    return token, expiration


def is_token_valid_for_uid(uid, token):
    """
    Vérifie si un token est encore valide pour un UID donné.
    """
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
        return False

    expiration_time = result[0]
    return expiration_time > datetime.now()


def validate_session_token(token):
    """
    Vérifie si un token est encore valide, et retourne l’UID correspondant s’il l’est.
    """
    print("[validate_session_token] Token reçu :", token)

    # ✅ Supprimer le préfixe "Bearer " si présent
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1].strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT UID, DATE_HEURE_FIN
            FROM SESSION_UTILISATEUR
            WHERE TOKEN = ?
        """, (token,))
        row = cursor.fetchone()
        print("[validate_session_token] Résultat SELECT :", row)

        cursor.close()
        conn.close()

        if row is None:
            return None  # Token inconnu

        uid, expires_at = row
        if expires_at < datetime.now():
            return None  # Session expirée

        return uid  # ✅ Token valide

    except Exception as e:
        return None
