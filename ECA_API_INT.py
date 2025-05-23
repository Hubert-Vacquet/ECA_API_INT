from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.routes.auth_routes import auth_bp
from app.routes.enedis_routes import enedis_bp
from app.routes.mail_routes import mail_bp
from app.routes.housing_routes import housing_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(housing_bp)
    app.register_blueprint(enedis_bp)
    app.register_blueprint(mail_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

