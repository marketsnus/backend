from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Promo(db.Model):
    __tablename__ = 'promo_images'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    original_filename = db.Column(db.String(255), nullable=False)
    s3_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'title': self.title,
            'description': self.description,
            's3_url': self.s3_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Bestsales(db.Model):
    __tablename__ = 'bestsales_products'
    
    id = db.Column(db.String(50), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    s3_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'filename': self.filename,
            's3_url': self.s3_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S.%f') if self.created_at else None
        }

class Metadata(db.Model):
    __tablename__ = 'metadata'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description
        }

class PaymentInfo(db.Model):
    __tablename__ = 'payment_info'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(200), nullable=False)
    recipient_name = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'account_number': self.account_number,
            'bank_name': self.bank_name,
            'recipient_name': self.recipient_name,
            'active': self.active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class NewProducts(db.Model):
    __tablename__ = 'new_products'
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    product_id = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    s3_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'name': self.name,
            'description': self.description,
            'product_id': self.product_id,
            'price': self.price,
            'category': self.category,
            's3_url': self.s3_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } 