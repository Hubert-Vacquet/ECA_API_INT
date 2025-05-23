# app/models/utilisateur.py

from app import db

class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<Utilisateur {self.nom}>'

def find_by_email(email):
    return Utilisateur.query.filter_by(email=email).first()

def update_user_login(user):
    # Logique pour mettre à jour les informations de connexion de l'utilisateur
    db.session.commit()

def create_new_user(nom, email, mot_de_passe):
    new_user = Utilisateur(nom=nom, email=email, mot_de_passe=mot_de_passe)
    db.session.add(new_user)
    db.session.commit()
    return new_user
