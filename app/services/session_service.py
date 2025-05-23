from datetime import datetime, timedelta

def insert_session(conn, uid, session_token, session_duration_minutes):
    """
    Insère une nouvelle session utilisateur avec date d'expiration.
    """
    cursor = conn.cursor()
    now = datetime.now()
    expiration = now + timedelta(minutes=session_duration_minutes)

    cursor.execute(
        """
        INSERT INTO SESSION_UTILISATEUR (UID, DATE_HEURE_DEBUT, DATE_HEURE_FIN, TOKEN)
        VALUES (?, ?, ?, ?)
        """,
        (uid, now, expiration, session_token)
    )
    conn.commit()

def is_session_valid(conn, session_token):
    """
    Vérifie si une session est encore valide (non expirée).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DATE_HEURE_FIN FROM SESSION_UTILISATEUR
        WHERE TOKEN = ?
        """,
        (session_token,)
    )
    result = cursor.fetchone()

    if result is None:
        return False  # Token inconnu

    expiration_time = result[0]
    return expiration_time > datetime.now()
