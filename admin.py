from flask import Flask, render_template, redirect, url_for, request, jsonify
import os
from flask_migrate import Migrate

# Импорты из модулей
from modules.models import db, Image, Product
from modules.image_tools import (
    upload_promo_image, delete_promo_image, update_promo_image,
    upload_product_image, delete_product_image, update_product_image
)

# Импорты из pages_py
from pages_py.api import get_promo, get_bestsales
from pages_py.pages import promo_page, bestsales_page

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'database.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.path.join(basedir, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)


upload_folder = os.path.join(app.static_folder, 'uploads')
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

db.init_app(app)
migrate = Migrate(app, db)

def init_database():
    """Инициализация базы данных"""
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/promo')
def promo_page_route():
    return promo_page(app, Image)

@app.route('/bestsales')
def bestsales_page_route():
    return bestsales_page(app, Product)

@app.route('/upload', methods=['POST'])
def upload_image():
    from pages_py.promo import upload_image_handler
    return upload_image_handler(app)

@app.route('/delete/<string:image_id>', methods=['POST'])
def delete_image(image_id):
    from pages_py.promo import delete_image_handler
    return delete_image_handler(image_id)

@app.route('/update/<string:image_id>', methods=['POST'])
def update_image(image_id):
    from pages_py.promo import update_image_handler
    return update_image_handler(image_id)

@app.route('/add_product', methods=['POST'])
def add_product():
    from pages_py.BestSales import upload_product_handler
    return upload_product_handler(app)

@app.route('/delete_product/<string:product_id>', methods=['POST'])
def delete_product(product_id):
    from pages_py.BestSales import delete_product_handler
    return delete_product_handler(product_id)

@app.route('/update_product/<string:product_id>', methods=['POST'])
def update_product(product_id):
    from pages_py.BestSales import update_product_handler
    return update_product_handler(product_id)

# API endpoints
@app.route('/api/promo', methods=['GET'])
def get_promo_route():
    return get_promo(app, Image)

@app.route('/api/bestSales', methods=['GET'])
def get_bestsales_route():
    return get_bestsales(app, Product)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 