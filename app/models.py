from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database
db = SQLAlchemy()

# User model to store user information
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # One-to-many relationship with uploaded files
    files = db.relationship('File', backref='owner', lazy=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Unified File model to handle uploaded files
class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chart_path = db.Column(db.String(255), nullable=True)  # Path to chart image
    result_url = db.Column(db.String(255), nullable=True)  # URL for result page
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, filename, file_path, user_id, chart_path=None, result_url=None):
        self.filename = filename
        self.file_path = file_path
        self.user_id = user_id
        self.chart_path = chart_path
        self.result_url = result_url
