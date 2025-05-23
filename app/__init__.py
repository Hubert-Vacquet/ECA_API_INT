# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configuration de l'application pour utiliser Firebird
    app.config['SQLALCHEMY_DATABASE_URI'] = 'firebird+fdb://user:password@localhost:3050/path/to/your/database.fdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialisation de SQLAlchemy avec l'application
    db.init_app(app)

    # Importation des blueprints
    from .routes.auth_routes import auth_bp

    # Enregistrement des blueprints
    app.register_blueprint(auth_bp)

    return app
