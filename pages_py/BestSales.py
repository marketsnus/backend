from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from s3_controller import upload_image_to_s3, delete_image_from_s3

template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
app = Flask(__name__, template_folder=template_dir)

# Создаем путь к папке databases
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_folder = os.path.join(basedir, 'databases')
if not os.path.exists(db_folder):
    os.makedirs(db_folder)

app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(db_folder, 'popular.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.path.join(basedir, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

load_dotenv()

class Product(db.Model):
    __tablename__ = 'product'  # Явно указываем имя таблицы
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    s3_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'filename': self.filename,
            's3_url': self.s3_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)