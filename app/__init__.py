from flask import Flask
from .extensions import db, migrate, login_manager
from .routes import main_bp
import os
from dotenv import load_dotenv


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

    app.register_blueprint(main_bp)

    return app
