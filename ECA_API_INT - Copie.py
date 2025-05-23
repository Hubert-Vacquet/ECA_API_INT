from flask import Flask, request, jsonify
from fdb import connect
import hashlib
import os
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import config

app = Flask(__name__)

# Générer une clé de cryptage
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Connexion à la base de données Firebird
def get_db_connection():
    return connect(
        dsn=config.DATABASE_PATH,
        user=config.USERNAME,
        password=config.PASSWORD
    )

# Crypter un mot de passe
def encrypt_password(password: str) -> str:
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password.decode()

# Décrypter un mot de passe
def decrypt_password(encrypted_password: str) -> str:
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode())
    return decrypted_password.decode()

# Envoyer un email
def send_email(to_address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@example.com'
    msg['To'] = to_address

    with smtplib.SMTP('smtp.example.com') as server:
        server.login('your_email@example.com', 'your_email_password')
        server.sendmail('your_email@example.com', to_address, msg.as_string())

# Générer un code de vérification
def generate_verification_code():
    return str(os.urandom(3).hex())[:6]

# Générer un jeton de session
def generate_session_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()

@app.route('/connexion', methods=['POST'])
def connexion():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and decrypt_password(user[5]) == password:
        session_token = generate_session_token()
        cur.execute("UPDATE UTILISATEUR SET DATE_DERNIERE_CONNEXION = ? WHERE IDENTIFIANT = ?", (datetime.now(), email))
        cur.execute("INSERT INTO SESSION_UTILISATEUR (UID, DATE_HEURE_DEBUT, DATE_HEURE_FIN) VALUES (?, ?, ?)",
                    (user[0], datetime.now(), datetime.now() + timedelta(minutes=config.SESSION_DURATION)))
        conn.commit()
        return jsonify({
            'code': 200,
            'uid': user[0],
            'identifiant': user[1],
            'nom': user[2],
            'prenom': user[3],
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

@app.route('/demandecompte', methods=['POST'])
def demandecompte():
    data = request.json
    email = data.get('email')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user:
        verification_code = generate_verification_code()
        session_token = generate_session_token()
        send_email(email, "Votre code à 6 chiffres", f"Votre code de vérification est : {verification_code}")
        return jsonify({
            'code': 200,
            'verification_code': verification_code,
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

@app.route('/creationcompte', methods=['POST'])
def creationcompte():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    nom = data.get('nom')
    prenom = data.get('prenom')
    cgu = data.get('cgu')
    newsletter = data.get('newsletter')
    offres_partenaires = data.get('offres_partenaires')
    verification_code = data.get('verification_code')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user:
        return jsonify({'code': 300})
    else:
        fournisseur = 'GOOGLE' if email.endswith(('@gmail.fr', '@gmail.com')) else 'EMAIL'
        encrypted_password = encrypt_password(password)
        cur.execute("INSERT INTO UTILISATEUR (IDENTIFIANT, FOURNISSEUR, DATE_CREATION, NOM, PRENOM, MOT_DE_PASSE, ACCEPTE_CGU, ABONNE_NEWSLETTER, ACCEPTE_OFFRES_PARTENAIRE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (email, fournisseur, datetime.now(), nom, prenom, encrypted_password, cgu, newsletter, offres_partenaires))
        conn.commit()
        session_token = generate_session_token()
        return jsonify({
            'code': 200,
            'token': session_token
        })

@app.route('/demandereinitmdp', methods=['POST'])
def demandereinitmdp():
    data = request.json
    email = data.get('email')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user:
        verification_code = generate_verification_code()
        session_token = generate_session_token()
        send_email(email, "Votre code à 6 chiffres", f"Votre code de vérification est : {verification_code}")
        return jsonify({
            'code': 200,
            'verification_code': verification_code,
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

@app.route('/reinitmdp', methods=['POST'])
def reinitmdp():
    data = request.json
    verification_code = data.get('verification_code')
    email = data.get('email')
    new_password = data.get('new_password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and user[8] == verification_code:
        encrypted_password = encrypt_password(new_password)
        cur.execute("UPDATE UTILISATEUR SET MOT_DE_PASSE = ? WHERE IDENTIFIANT = ?", (encrypted_password, email))
        conn.commit()
        session_token = generate_session_token()
        return jsonify({
            'code': 200,
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

@app.route('/connexiong', methods=['POST'])
def connexiong():
    data = request.json
    nom = data.get('nom')
    prenom = data.get('prenom')
    email = data.get('email')
    session_token = data.get('token')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user:
        cur.execute("UPDATE UTILISATEUR SET DATE_DERNIERE_CONNEXION = ? WHERE IDENTIFIANT = ?", (datetime.now(), email))
        cur.execute("INSERT INTO SESSION_UTILISATEUR (UID, DATE_HEURE_DEBUT, DATE_HEURE_FIN) VALUES (?, ?, ?)",
                    (user[0], datetime.now(), datetime.now() + timedelta(minutes=config.SESSION_DURATION)))
        conn.commit()
        return jsonify({
            'code': 200,
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

if __name__ == '__main__':
    app.run(debug=True)
