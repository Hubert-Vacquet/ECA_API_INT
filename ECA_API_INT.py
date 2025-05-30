from flask import Flask, request, jsonify
from flask_cors import CORS
from app.config import Config
from app.routes.auth_routes import auth_bp
from app.routes.enedis_routes import enedis_bp
from app.routes.mail_routes import mail_bp
from app.routes.housing_routes import housing_bp
from app.services.session_service import is_token_valid_for_uid
from app.services.token_service import clean_expired_sessions
from app.services.session_service import validate_session_token


import sys
import os
from flask import g

EXCLUDED_ENDPOINTS = [
    '/connexion',
    '/demandecompte',
    '/creationcompte',
    '/ValidationCreationCompte',
    '/demandereinitmdp',
    '/reinitmdp',
    '/api/send_test_email',
    '/validate_enedis'
]

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    clean_expired_sessions()  # Nettoie au démarrage
    CORS(app)

    # Middleware de session
    @app.before_request
    def check_session():
        path = request.path
        if any(path.startswith(endpoint) for endpoint in EXCLUDED_ENDPOINTS):
            return  # Pas de vérification nécessaire

        token = request.headers.get('Authorization')
        uid = request.headers.get('UID')

        if not token or not uid:
            return jsonify({'code': 401, 'message': 'Session manquante'}), 401

        user_id = validate_session_token(token)
        if not user_id:
            return jsonify({"message": "Session expirée ou invalide"}), 401
        g.user_id = user_id

    # Enregistrement des routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(housing_bp)
    app.register_blueprint(enedis_bp)
    app.register_blueprint(mail_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
