from flask import Blueprint, request, jsonify
from app.utils.db import get_db_connection
from app.services import auth_service, mail_service, crypto_service, token_service
from app.config import Config
from datetime import datetime, timedelta
from firebase_admin import auth as firebase_auth
from models.db import db
from models.sessions import Session  # Ton modèle de session
from models.users import User  # Ton modèle User

import uuid
import os

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

@auth_bp.route('/auth/firebase-login', methods=['POST'])
def firebase_login():
    data = request.get_json()
    id_token = data.get('idToken')

    if not id_token:
        return jsonify({'message': 'Token manquant'}), 400

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')

        # Vérifie si l'utilisateur existe déjà, sinon crée-le
        user = User.query.filter_by(firebase_uid=uid).first()
        if not user:
            user = User(firebase_uid=uid, email=email)
            db.session.add(user)
            db.session.commit()

        # Crée une session
        session_token = str(uuid.uuid4())
        expiration = datetime.utcnow() + timedelta(minutes=int(os.getenv("SESSION_DURATION", 5)))
        new_session = Session(user_id=user.id, token=session_token, expires_at=expiration)
        db.session.add(new_session)
        db.session.commit()

        return jsonify({'token': session_token, 'user': {'uid': user.firebase_uid, 'email': user.email}})

    except Exception as e:
        print("Erreur Firebase Login :", e)
        return jsonify({'message': 'Token Firebase invalide'}), 401

@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    data = request.get_json()
    uid = data.get("uid")
    token = data.get("session_token")

    if not uid or not token:
        return jsonify({"error": "UID ou token manquant"}), 400

    try:
        # Récupère l'utilisateur via firebase_uid
        user = User.query.filter_by(firebase_uid=uid).first()
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        # Supprime la session correspondante
        session = Session.query.filter_by(user_id=user.id, token=token).first()
        if not session:
            return jsonify({"error": "Session introuvable"}), 404

        db.session.delete(session)
        db.session.commit()

        return jsonify({"status": "success", "message": "Déconnexion réussie."}), 200

    except Exception as e:
        db.session.rollback()
        print("Erreur lors de la déconnexion :", e)
        return jsonify({"error": "Erreur serveur lors de la déconnexion."}), 500
