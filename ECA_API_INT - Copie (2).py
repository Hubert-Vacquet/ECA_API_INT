from flask import Flask, request, jsonify
from flask_cors import CORS
from config import DATABASE_PATH, DB_USERNAME, PASSWORD, ENCRYPTION_KEY, SESSION_DURATION, PASSWORD_SRV_MAIL
from fdb import connect
import hashlib
import os
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import uuid
import random

app = Flask(__name__)
CORS(app)  # Ajoutez cette ligne pour activer CORS pour toutes les routes

# Récupération de la clé de cryptage des mots de passe utilisateurs
cipher_suite = Fernet(ENCRYPTION_KEY)

# Connexion à la base de données Firebird
def get_db_connection():
    return connect(
        dsn=DATABASE_PATH,
        user=DB_USERNAME,
        password=PASSWORD
    )

# Crypter un mot de passe
def encrypt_password(password: str) -> str:
    encrypted_password = cipher_suite.encrypt(password.encode())
    encrypted_password_str = encrypted_password.decode()
    print(f"Encrypted password: {encrypted_password_str}, Length: {len(encrypted_password_str)}")
    return encrypted_password_str

# Décrypter un mot de passe
def decrypt_password(encrypted_password: str) -> str:
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password.encode())
        return decrypted_password.decode()
    except Exception as e:
        print(f"Error decrypting password: {e}")
        raise

# Envoyer un email
def send_email(to_address, subject, body):
    # Informations de l'expéditeur
    email_expediteur = "hubert.vacquet@gmail.com"
    #PASSWORD_SRV_MAIL = "ofoa hoqi nmfq tmhe"  # Mot de passe de l'expéditeur (à remplacer par une variable d'environnement ou un autre moyen sécurisé)
    #mot_de_passe = os.getenv("EMAIL_PASSWORD")  # Utilisation d'une variable d'environnement pour le mot de passe

    # Création du message
    message = MIMEMultipart()
    message["From"] = email_expediteur
    message["To"] = to_address
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Connexion au serveur Gmail
        serveur = smtplib.SMTP("smtp.gmail.com", 587)
        serveur.starttls()
        serveur.login(email_expediteur, PASSWORD_SRV_MAIL)
        serveur.sendmail(email_expediteur, to_address, message.as_string())
        serveur.quit()
        print("E-mail envoyé avec succès !")
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi : {e}")
        return False

# Générer un code de vérification de 6 chiffres
def generate_verification_code():
    return ''.join(random.choices('0123456789', k=6))

# Générer un jeton de session
def generate_session_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()

# Générer un UID unique
def generate_uid():
    return str(uuid.uuid4())

@app.route('/connexion', methods=['POST'])
def connexion():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()
    print(f"user: {user}")

    if user:
        try:
            encrypted_password_from_db = user[7]
            decrypted_password = decrypt_password(encrypted_password_from_db)
            if decrypted_password == password:
                session_token = generate_session_token()
                uid = user[4]  # Assurez-vous d'utiliser la bonne valeur de UID
                print(f"UID for insertion: {uid}")  # Ajoutez ce log pour vérifier la valeur de UID
                cur.execute("UPDATE UTILISATEUR SET DATE_DERNIERE_CONNEXION = ? WHERE IDENTIFIANT = ?", (datetime.now(), email))
                cur.execute("INSERT INTO SESSION_UTILISATEUR (UID, DATE_HEURE_DEBUT, DATE_HEURE_FIN, TOKEN) VALUES (?, ?, ?, ?)",
             (uid, datetime.now(), datetime.now() + timedelta(minutes=SESSION_DURATION), session_token))
                conn.commit()
                print(f"identifiant: {user[1]}, nom: {user[2]}, prenom: {user[3]}")  # Ajoutez ce log pour vérifier les valeurs
                return jsonify({
                    'code': 200,
                    'uid': uid,
                    'identifiant': user[0],
                    'nom': user[5],
                    'prenom': user[6],
                    'token': session_token
                })
            else:
                return jsonify({'code': 300})
        except Exception as e:
            print(f"Error decrypting password: {e}")  # Ajoutez ce log pour vérifier les erreurs de déchiffrement
            return jsonify({'code': 500, 'message': 'Internal server error'})
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
    
    # Log des valeurs reçues
    print('Received data:', data)
    print('Tested Data:', email, password, nom, prenom, cgu, newsletter, offres_partenaires)

    # Vérifiez que toutes les valeurs nécessaires sont présentes
    if any(value is None for value in [email, password, nom, prenom, cgu, newsletter, offres_partenaires]):
        missing_values = [key for key, value in data.items() if value is None]
        return jsonify({'code': 400, 'message': f'Valeurs manquantes : {", ".join(missing_values)}'})

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    if user and user[12] == 1:  # Vérifiez si le compte est déjà vérifié
        return jsonify({'code': 300, 'message': f'Compte déjà existant pour l\'email {email}'})
    else:
        # Générer un code de vérification
        verification_code = generate_verification_code()
        send_email(email, "Votre code à 6 chiffres", f"Votre code de vérification est : {verification_code}")

        uid = generate_uid()  # Générer un UID unique
        fournisseur = 'GOOGLE' if email.endswith(('@gmail.fr', '@gmail.com')) else 'EMAIL'
        encrypted_password = encrypt_password(password)
        compte_verifie = 0  # Par défaut, le compte n'est pas vérifié

        if user:
            # Mettre à jour l'utilisateur existant
            cur.execute("""
                UPDATE UTILISATEUR
                SET NOM = ?, PRENOM = ?, MOT_DE_PASSE = ?, ACCEPTE_CGU = ?, ABONNE_NEWSLETTER = ?, ACCEPTE_OFFRES_PARTENAIRE = ?, CODE_VERIFICATION = ?, EST_VERIFIE = ?
                WHERE IDENTIFIANT = ?
            """, (nom, prenom, encrypted_password, cgu, newsletter, offres_partenaires, verification_code, compte_verifie, email))
        else:
            # Insérer un nouvel utilisateur
            cur.execute("""
                INSERT INTO UTILISATEUR (UID, IDENTIFIANT, FOURNISSEUR, DATE_CREATION, NOM, PRENOM, MOT_DE_PASSE, ACCEPTE_CGU, ABONNE_NEWSLETTER, ACCEPTE_OFFRES_PARTENAIRE, CODE_VERIFICATION, EST_VERIFIE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, email, fournisseur, datetime.now(), nom, prenom, encrypted_password, cgu, newsletter, offres_partenaires, verification_code, compte_verifie))

        conn.commit()

        return jsonify({
            'code': 200,
            'message': 'Compte créé avec succès'
        })

@app.route('/ValidationCreationCompte', methods=['POST'])
def ValidationCreationCompte():
    data = request.json
    email = data.get('email')
    verification_code = data.get('verification_code')

    if not email or not verification_code:
        return jsonify({'code': 400, 'message': 'Email ou code de vérification manquant'})

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT CODE_VERIFICATION FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()

    # Log des valeurs reçues
    print('Received data for validation:', data)
    print('Donnees utilisateur en base:', user)
    print('code temporaire en base:', user[0])
    print('code temporaire saisi:', verification_code)

    if user and user[0] == verification_code:
        cur.execute("UPDATE UTILISATEUR SET CODE_VERIFICATION = NULL, EST_VERIFIE = 1 WHERE IDENTIFIANT = ?", (email,))
        conn.commit()
        return jsonify({'code': 200, 'message': 'Compte vérifié avec succès'})
    else:
        return jsonify({'code': 300, 'message': 'Code de vérification invalide'})

@app.route('/demandereinitmdp', methods=['POST'])
def demandereinitmdp():
    data = request.json
    email = data.get('email')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()
    print('user:', user)

    if user:
        verification_code = generate_verification_code()
        cur.execute("UPDATE UTILISATEUR SET CODE_VERIFICATION = ? WHERE IDENTIFIANT = ?", (verification_code, email))
        conn.commit()

        send_email(email, "Votre code à 6 chiffres", f"Votre code de vérification est : {verification_code}")
        return jsonify({
            'code': 200
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
    cur.execute("SELECT CODE_VERIFICATION FROM UTILISATEUR WHERE IDENTIFIANT = ?", (email,))
    user = cur.fetchone()
    print('code temporaire en base:', user[0])
    print('code temporaire saisi:', verification_code)

    if user and user[0] == verification_code:
        encrypted_password = encrypt_password(new_password)
        cur.execute("UPDATE UTILISATEUR SET MOT_DE_PASSE = ?, CODE_VERIFICATION = NULL WHERE IDENTIFIANT = ?", (encrypted_password, email))
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
                    (user[0], datetime.now(), datetime.now() + timedelta(minutes=SESSION_DURATION)))
        conn.commit()
        return jsonify({
            'code': 200,
            'token': session_token
        })
    else:
        return jsonify({'code': 300})

if __name__ == '__main__':
    app.run(debug=True)
