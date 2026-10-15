# models.py - Database Models
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200))
    google_id = db.Column(db.String(100), unique=True)
    is_google_user = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(500), default='default_avatar.png')
    bio = db.Column(db.Text, default='Plant enthusiast 🌱')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploads = db.relationship('Upload', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_google_user': self.is_google_user,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Upload(db.Model):
    __tablename__ = 'uploads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    image_path = db.Column(db.String(500), nullable=False)
    prediction = db.Column(db.String(200), index=True)
    confidence = db.Column(db.Float)
    severity = db.Column(db.String(20), default='LOW', index=True)
    symptoms = db.Column(db.Text)
    cause = db.Column(db.Text)
    treatment = db.Column(db.Text)
    organic = db.Column(db.Text)
    prevention = db.Column(db.Text)
    care_tips = db.Column(db.Text)
    is_healthy = db.Column(db.Boolean, default=False, index=True)
    disease_code = db.Column(db.String(50))
    analyzed_by = db.Column(db.String(50), default='AI v2.0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'severity': self.severity,
            'symptoms': self.symptoms,
            'cause': self.cause,
            'treatment': self.treatment,
            'organic': self.organic,
            'prevention': self.prevention,
            'is_healthy': self.is_healthy,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False, index=True)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)