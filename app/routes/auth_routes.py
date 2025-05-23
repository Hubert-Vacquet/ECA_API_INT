from flask import Blueprint, request, jsonify
from app.utils.db import get_db_connection
from app.services import auth_service, mail_service, crypto_service, token_service
from app.config import Config
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/connexion', methods=['POST'])
def login():
    conn = get_db_connection()
    data = request.json
    return auth_service.login_user(data, conn, Config.ENCRYPTION_KEY)

@auth_bp.route('/demandecompte', methods=['POST'])
def demande_creation_compte():
    conn = get_db_connection()
    data = request.json
    email = data.get('email')
    user = auth_service.find_user_by_email(conn, email)

    if user:
        code = auth_service.generate_verification_code()
        token = token_service.generate_session_token()
        mail_service.send_verification_code(email, code)
        return jsonify({'code': 200, 'verification_code': code, 'token': token})
    return jsonify({'code': 300})

@auth_bp.route('/creationcompte', methods=['POST'])
def creation_compte():
    conn = get_db_connection()
    data = request.json
    return auth_service.create_user_account(data, conn, Config.ENCRYPTION_KEY)

@auth_bp.route('/ValidationCreationCompte', methods=['POST'])
def validation_creation_compte():
    conn = get_db_connection()
    data = request.json
    return auth_service.validate_account_creation(data, conn)

@auth_bp.route('/demandereinitmdp', methods=['POST'])
def demande_reinit_mdp():
    conn = get_db_connection()
    data = request.json
    return auth_service.request_password_reset(data, conn)

@auth_bp.route('/reinitmdp', methods=['POST'])
def reinit_mdp():
    conn = get_db_connection()
    data = request.json
    return auth_service.reset_password(data, conn, Config.ENCRYPTION_KEY)
