from flask import jsonify
from app.services.crypto_service import encrypt_password, decrypt_password
from app.services.token_service import generate_session_token
from app.services.mail_service import send_verification_code
from app.models.utilisateur import find_by_email, update_user_login
from app.services.session_service import insert_session
from app.config import Config

from datetime import datetime
import uuid
import random

def generate_verification_code():
    return ''.join(random.choices('0123456789', k=6))

def login_user(data, conn, encryption_key):
    email = data.get('email')
    password = data.get('password')

    user = find_by_email(conn, email)
    print("User found: ", user)
    if user:
        encrypted_password_from_db = user[7]
        decrypted_password = decrypt_password(encrypted_password_from_db, encryption_key)
        if decrypted_password == password:
            session_token = generate_session_token()
            uid = user[4]
            update_last_connection(conn, email)
            insert_session(conn, uid, session_token, Config.SESSION_DURATION)
            return {
                'code': 200,
                'uid': uid,
                'identifiant': user[0],
                'nom': user[5],
                'prenom': user[6],
                'token': session_token
            }
        else:
            return {'code': 300}
    else:
        return {'code': 300}

def find_by_email(conn, email):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cursor.fetchone()
    cursor.close()
    return user

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
    password_enc = encrypt_password(password, key)

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
    send_verification_code(email, code)
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
        return jsonify({'code': 200, 'message': 'Compte vérifié'})
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
        send_verification_code(email, code)
        return jsonify({'code': 200})
    return jsonify({'code': 300})

def reset_password(data, conn, key):
    email = data.get('email')
    new_password = data.get('new_password')
    code = data.get('verification_code')

    cur = conn.cursor()
    cur.execute("SELECT CODE_VERIFICATION FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and user[0] == code:
        password_enc = encrypt_password(new_password, key)
        cur.execute("UPDATE UTILISATEUR SET MOT_DE_PASSE = ?, CODE_VERIFICATION = NULL WHERE IDENTIFIANT = ?", (password_enc, email))
        conn.commit()
        token = generate_session_token()
        return jsonify({'code': 200, 'token': token})
    return jsonify({'code': 300})

from datetime import datetime

def update_last_connection(conn, email):
    cursor = conn.cursor()
    cursor.execute("UPDATE UTILISATEUR SET DATE_DERNIERE_CONNEXION = ? WHERE IDENTIFIANT = ?", (datetime.now(), email))
    conn.commit()
    cursor.close()
