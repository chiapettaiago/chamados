from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' ou 'user'
    is_active = db.Column(db.Boolean, default=True)
    phone_e164 = db.Column(db.String(20), nullable=True)  # WhatsApp em E.164, ex.: 5599999999999
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship('Ticket', backref='creator', lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='aberto')  # aberto, em_andamento, resolvido, fechado
    priority = db.Column(db.String(20), default='media')  # baixa, media, alta, critica
    vendor = db.Column(db.String(120), nullable=True)  # firma terceirizada
    assignee = db.Column(db.String(120), nullable=True)  # responsável interno

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interactions = db.relationship('Interaction', backref='ticket', lazy=True, cascade='all, delete-orphan')

    @property
    def last_vendor_contact_at(self):
        if not self.vendor:
            return None
        vendor_key = (self.vendor or '').strip().lower()
        if not vendor_key:
            return None
        times = [i.created_at for i in self.interactions if i.author and vendor_key in i.author.strip().lower()]
        return max(times) if times else None

    @property
    def last_contact_at(self):
        if self.interactions:
            return max((i.created_at for i in self.interactions), default=self.created_at)
        return self.created_at

    @property
    def is_stale_24h(self) -> bool:
        try:
            delta = datetime.utcnow() - (self.last_contact_at or self.created_at)
        except Exception:
            return False
        # Considerar alerta apenas se não estiver fechado
        return self.status != 'fechado' and delta.total_seconds() > 24*3600


class Interaction(db.Model):
    __tablename__ = 'interactions'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(120), nullable=False)  # nome do autor (terceirizada/usuário)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
