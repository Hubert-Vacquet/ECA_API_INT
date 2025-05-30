from flask import jsonify
from app.services import crypto_service, token_service, mail_service, session_service
from app.models.utilisateur import find_by_email, update_user_login
from app.config import Config
from datetime import datetime
import uuid
import random


def generate_verification_code():
    return ''.join(random.choices('0123456789', k=6))


def login_user(data, conn, encryption_key):
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'code': 400, 'message': 'Champs manquants'}), 400

    cur = conn.cursor()
    cur.execute("SELECT UID, MOT_DE_PASSE FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify({'code': 401, 'message': 'Utilisateur non trouvé'}), 401

    uid, encrypted_password = user

    if not crypto_service.check_password(password, encrypted_password, encryption_key):
        return jsonify({'code': 403, 'message': 'Mot de passe incorrect'}), 403

    token = token_service.create_user_session(uid)
    if not token:
        return jsonify({'code': 500, 'message': 'Erreur lors de la création de session'}), 500

    return jsonify({'code': 200, 'message': 'Connexion réussie', 'uid': uid, 'token': token})


def create_user_account(data, conn, key):
    email = data.get('email')
    password = data.get('password')
    nom = data.get('nom')
    prenom = data.get('prenom')
    cgu = data.get('cgu')
    newsletter = data.get('newsletter')
    offres = data.get('offres_partenaires')

    if any(value is None for value in [email, password, nom, prenom, cgu, newsletter, offres]):
        return jsonify({'code': 400, 'message': 'Champs manquants'})

    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    code = generate_verification_code()
    uid = str(uuid.uuid4())
    fournisseur = 'GOOGLE' if email.endswith(('@gmail.com', '@gmail.fr')) else 'EMAIL'
    password_enc = crypto_service.encrypt_password(password, key)

    if user:
        cur.execute("""
            UPDATE UTILISATEUR SET NOM=?, PRENOM=?, MOT_DE_PASSE=?, ACCEPTE_CGU=?, ABONNE_NEWSLETTER=?,
            ACCEPTE_OFFRES_PARTENAIRE=?, CODE_VERIFICATION=?, EST_VERIFIE=0 WHERE IDENTIFIANT=?
        """, (nom, prenom, password_enc, cgu, newsletter, offres, code, email))
    else:
        cur.execute("""
            INSERT INTO UTILISATEUR (UID, IDENTIFIANT, FOURNISSEUR, DATE_CREATION, NOM, PRENOM,
            MOT_DE_PASSE, ACCEPTE_CGU, ABONNE_NEWSLETTER, ACCEPTE_OFFRES_PARTENAIRE, CODE_VERIFICATION, EST_VERIFIE)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (uid, email, fournisseur, datetime.now(), nom, prenom, password_enc, cgu, newsletter, offres, code))

    conn.commit()
    cur.close()

    try:
        mail_service.send_verification_code(email, code)
    except Exception:
        return jsonify({'code': 500, 'message': 'Erreur lors de l’envoi de l’email'}), 500

    return jsonify({'code': 200, 'message': 'Compte créé'})


def validate_account_creation(data, conn):
    email = data.get('email')
    code = data.get('verification_code')

    cur = conn.cursor()
    cur.execute("SELECT CODE_VERIFICATION FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and user[0] == code:
        cur.execute("UPDATE UTILISATEUR SET CODE_VERIFICATION = NULL, EST_VERIFIE = 1 WHERE IDENTIFIANT = ?", (email,))
        conn.commit()
        cur.close()
        return jsonify({'code': 200, 'message': 'Compte vérifié'})

    cur.close()
    return jsonify({'code': 300, 'message': 'Code invalide'})


def request_password_reset(data, conn):
    email = data.get('email')

    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user:
        code = generate_verification_code()
        cur.execute("UPDATE UTILISATEUR SET CODE_VERIFICATION = ? WHERE IDENTIFIANT = ?", (code, email))
        conn.commit()
        cur.close()
        try:
            mail_service.send_verification_code(email, code)
        except Exception:
            return jsonify({'code': 500, 'message': 'Erreur lors de l’envoi de l’email'}), 500
        return jsonify({'code': 200})

    cur.close()
    return jsonify({'code': 300})


def reset_password(data, conn, key):
    email = data.get('email')
    new_password = data.get('new_password')
    code = data.get('verification_code')

    cur = conn.cursor()
    cur.execute("SELECT CODE_VERIFICATION FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and user[0] == code:
        password_enc = crypto_service.encrypt_password(new_password, key)
        cur.execute("UPDATE UTILISATEUR SET MOT_DE_PASSE = ?, CODE_VERIFICATION = NULL WHERE IDENTIFIANT = ?", (password_enc, email))
        conn.commit()
        cur.close()
        token = token_service.create_user_session(email)
        return jsonify({'code': 200, 'token': token})

    cur.close()
    return jsonify({'code': 300})


def update_last_connection(conn, email):
    cur = conn.cursor()
    cur.execute("UPDATE UTILISATEUR SET DATE_DERNIERE_CONNEXION = ? WHERE IDENTIFIANT = ?", (datetime.now(), email))
    conn.commit()
    cur.close()
