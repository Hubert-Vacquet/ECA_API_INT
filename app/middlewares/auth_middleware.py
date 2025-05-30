from functools import wraps
from flask import request, jsonify
from app.services.session_service import is_session_valid

def require_valid_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        uid = request.headers.get('UID')

        if not token or not uid:
            return jsonify({'code': 401, 'message': 'Session manquante'}), 401

        if not is_session_valid(uid, token):
            return jsonify({'code': 440, 'message': 'Session expirée ou invalide'}), 440  # 440 = Login Timeout (non standard mais clair)

        return f(*args, **kwargs)
    return decorated_function
