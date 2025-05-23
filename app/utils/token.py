import secrets

def generate_session_token(length: int = 32) -> str:
    """
    Génère un token de session sécurisé.

    :param length: Longueur du token (en bytes, avant encodage).
    :return: Token encodé en base64, prêt à être utilisé comme identifiant de session.
    """
    return secrets.token_urlsafe(length)
