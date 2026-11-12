"""
Database Models for ReadEase
Defines Users, Documents, Summaries, Vocabulary, and QuizResults tables.
"""
from datetime import datetime, timezone
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login helper to load the active user from session ID."""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """Student user account model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    documents = db.relationship('Document', backref='owner', lazy=True, cascade='all, delete-orphan')
    summaries = db.relationship('Summary', backref='user', lazy=True, cascade='all, delete-orphan')
    vocabulary_items = db.relationship('Vocabulary', backref='user', lazy=True, cascade='all, delete-orphan')
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes password using secure PBKDF2/SHA256."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        """Generates a secure, time-limited token for password reset (valid for 1 hour)."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, max_age=3600):
        """Verifies the reset token; returns the User if valid, else None."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt='password-reset-salt', max_age=max_age)
        except (SignatureExpired, BadTimeSignature):
            return None
        return User.query.get(data.get('user_id'))

    def __repr__(self):
        return f"<User {self.email}>"


class Document(db.Model):
    """Uploaded PDF document model."""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    summaries = db.relationship('Summary', backref='document', lazy=True, cascade='all, delete-orphan')
    vocabulary_items = db.relationship('Vocabulary', backref='document', lazy=True, cascade='all, delete-orphan')
    quiz_results = db.relationship('QuizResult', backref='document', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Document {self.original_filename} (User: {self.user_id})>"


class Summary(db.Model):
    """Extractive summary record for an uploaded document."""
    __tablename__ = 'summaries'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    summary_text = db.Column(db.Text, nullable=False)
    summary_length = db.Column(db.String(50), nullable=False, default='medium')  # short, medium, long
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Summary doc_id={self.document_id} length={self.summary_length}>"


class Vocabulary(db.Model):
    """Saved difficult vocabulary words for a student."""
    __tablename__ = 'vocabulary'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=True, index=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Vocabulary {self.word} (User: {self.user_id})>"


class QuizResult(db.Model):
    """Quiz performance record for a document."""
    __tablename__ = 'quiz_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<QuizResult score={self.score}/{self.total_questions}>"
