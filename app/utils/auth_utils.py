from flask import request, g, jsonify
from functools import wraps
from ..services.session_service import validate_session_token

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        print("[require_auth] Décorateur exécuté ✅")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'message': 'Token manquant ou invalide'}), 401

        token = auth_header.replace("Bearer ", "").strip()
        user_id = validate_session_token(token)

        if not user_id:
            return jsonify({'message': 'Session expirée ou invalide'}), 401

        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function
