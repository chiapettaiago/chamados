from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):
    # Import local para evitar import circular
    from .models import User
    return User.query.get(int(user_id))
