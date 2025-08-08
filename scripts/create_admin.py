from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(email='admin@empresa.com').first():
        u = User(name='Admin', email='admin@empresa.com', role='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print('Admin criado:', u.email)
    else:
        print('Admin já existe')
