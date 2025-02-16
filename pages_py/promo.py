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
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(db_folder, 'images.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.path.join(basedir, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

load_dotenv()

class Image(db.Model):
    __tablename__ = 'image'  # Явно указываем имя таблицы
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    s3_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'title': self.title,
            'description': self.description,
            's3_url': self.s3_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    images = Image.query.order_by(Image.created_at.desc()).all()
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400

    file = request.files['image']
    title = request.form.get('title', '')
    description = request.form.get('description', '')

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    try:
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{file_id}_{original_filename}"

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        if upload_image_to_s3(temp_path, filename):
            s3_url = f"https://sqwonkerb.storage.yandexcloud.net/{filename}"

            new_image = Image(
                id=file_id,
                filename=filename,
                original_filename=original_filename,
                title=title,
                description=description,
                s3_url=s3_url
            )
            db.session.add(new_image)
            db.session.commit()

            os.remove(temp_path)
            return jsonify(new_image.to_dict()), 200
        else:
            os.remove(temp_path)
            return jsonify({'error': 'Ошибка загрузки в S3'}), 500

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<string:image_id>', methods=['POST'])
def delete_image(image_id):
    try:
        image = Image.query.get_or_404(image_id)
        
        # Сначала удаляем из S3
        if delete_image_from_s3(image.filename):
            # Если удаление из S3 успешно, удаляем из БД
            db.session.delete(image)
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/update/<string:image_id>', methods=['POST'])
def update_image(image_id):
    try:
        image = Image.query.get_or_404(image_id)
        image.title = request.form.get('title', image.title)
        image.description = request.form.get('description', image.description)
        db.session.commit()
        return jsonify(image.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo', methods=['GET'])
def get_products():
    try:
        products = Image.query.order_by(Image.created_at.desc()).all()
        return jsonify({
            'success': True,
            'products': [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print(f"Запуск приложения...")
    app.run(debug=True)