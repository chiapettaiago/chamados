from flask import Flask
from .extensions import db, migrate, login_manager
from .routes import main_bp
import os
from dotenv import load_dotenv
import json


def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'unsafe-dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importar modelos para registrar metadata nas migrações
    from . import models  # noqa: F401

    # Filtro Jinja para formatar timedeltas como HH:MM:SS
    def format_timedelta(value):
        try:
            total_seconds = int(value.total_seconds())
        except Exception:
            return ''
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    app.jinja_env.filters['format_timedelta'] = format_timedelta

    # Disponibilizar config do Firebase nas templates
    @app.context_processor
    def inject_firebase_config():
        return {
            'FIREBASE_CONFIG': {
                'apiKey': os.getenv('FIREBASE_API_KEY'),
                'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
                'projectId': os.getenv('FIREBASE_PROJECT_ID'),
                'appId': os.getenv('FIREBASE_APP_ID'),
                'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
            }
        }

    # Inicializar Firebase Admin (verificação de ID token no backend)
    app.config['FIREBASE_ADMIN_READY'] = False
    try:
        import firebase_admin  # type: ignore
        from firebase_admin import credentials  # type: ignore
        cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE')
        cred = None
        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        if cred and not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            app.config['FIREBASE_ADMIN_READY'] = True
    except Exception:
        # Sem credenciais ou pacote não instalado; login Google ficará inativo no backend
        pass

    app.register_blueprint(main_bp)

    return app
