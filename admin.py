from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
import uuid
from werkzeug.utils import secure_filename
from api import get_promo, get_bestsales
from pages import promo_page, bestsales_page
from image_tools import (
    upload_promo_image, delete_promo_image, update_promo_image,
    upload_product_image, delete_product_image, update_product_image
)

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'images.db'),
    SQLALCHEMY_BINDS={
        'bestsales': 'sqlite:///' + os.path.join(basedir, 'popular.db')
    },
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.path.join(basedir, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from pages_py.promo import app as promo_app, Image, db as promo_db
from pages_py.BestSales import app as bestsales_app, Product, db as bestsales_db

def init_databases():
    """Инициализация всех баз данных"""
    try:
        with promo_app.app_context():
            promo_db.create_all()
        with bestsales_app.app_context():
            bestsales_db.create_all()
    except Exception as e:
        print(f"Ошибка при инициализации баз данных: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/promo')
def promo_page_route():
    return promo_page(promo_app, Image)

@app.route('/bestsales')
def bestsales_page_route():
    return bestsales_page(bestsales_app, Product)

@app.route('/upload', methods=['POST'])
def upload_image():
    return upload_promo_image(app, promo_app, Image, promo_db)

@app.route('/delete/<string:image_id>', methods=['POST'])
def delete_image(image_id):
    return delete_promo_image(promo_app, Image, promo_db, image_id)

@app.route('/update/<string:image_id>', methods=['POST'])
def update_image(image_id):
    return update_promo_image(promo_app, Image, promo_db, image_id)

@app.route('/add_product', methods=['POST'])
def add_product():
    return upload_product_image(app, bestsales_app, Product, bestsales_db)

@app.route('/delete_product/<string:product_id>', methods=['POST'])
def delete_product(product_id):
    return delete_product_image(bestsales_app, Product, bestsales_db, product_id)

@app.route('/update_product/<string:product_id>', methods=['POST'])
def update_product(product_id):
    return update_product_image(bestsales_app, Product, bestsales_db, product_id)


# API endpoints
@app.route('/api/promo', methods=['GET'])
def get_promo_route():
    return get_promo(promo_app, Image)

@app.route('/api/bestSales', methods=['GET'])
def get_bestsales_route():
    return get_bestsales(bestsales_app, Product)

if __name__ == '__main__':
    init_databases()
    app.run(debug=True) 