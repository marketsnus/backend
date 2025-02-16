from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
import os
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from login.login import before_request, login_function
from modules.models import db, Promo, Bestsales, User
from modules.image_tools import (
    upload_promo_image, delete_promo_image, update_promo_image,
    upload_product_image, delete_product_image, update_product_image
)
from pages_py.api import get_promo, get_bestsales
from pages_py.pages import promo_page, bestsales_page
from pages_py.metadata import metadata_page, update_metadata_handler, delete_category_image
from pages_py.payment import payment_page, add_payment_info, delete_payment_info

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'database.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=os.path.join(basedir, 'static', 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SECRET_KEY='admin'
)

upload_folder = os.path.join(app.static_folder, 'uploads')
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

db.init_app(app)
migrate = Migrate(app, db)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_router'

def init_database():
    """Инициализация базы данных"""
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {str(e)}")
        raise

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def before_request_router():
    return before_request()

@app.route('/login', methods=['GET', 'POST'])
def login_router():
    return login_function()

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_router'))


@app.route('/')
@login_required
def index():
    return render_template('base.html')

@app.route('/promo')
@login_required
def promo_page_route():
    return promo_page(app, Promo)

@app.route('/bestsales')
@login_required
def bestsales_page_route():
    return bestsales_page(app, Bestsales)

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
    return get_promo(app, Promo)

@app.route('/api/bestSales', methods=['GET'])
def get_bestsales_route():
    return get_bestsales(app, Bestsales)

@app.route('/metadata')
@login_required
def metadata_page_route():
    return metadata_page()

@app.route('/update_metadata', methods=['POST'])
@login_required
def update_metadata():
    return update_metadata_handler()

@app.route('/delete_category_image/<category>', methods=['POST'])
@login_required
def delete_category_image_route(category):
    return delete_category_image(category)

@app.route('/api/metadata', methods=['GET'])
def get_metadata_route():
    from pages_py.metadata import get_metadata_api
    return get_metadata_api()

@app.route('/payment')
@login_required
def payment_page_route():
    return payment_page()

@app.route('/add_payment', methods=['POST'])
@login_required
def add_payment():
    return add_payment_info()

@app.route('/delete_payment/<int:payment_id>', methods=['POST'])
@login_required
def delete_payment(payment_id):
    return delete_payment_info(payment_id)

@app.route('/toggle_payment/<int:payment_id>', methods=['POST'])
@login_required
def toggle_payment(payment_id):
    from pages_py.payment import toggle_payment_status
    return toggle_payment_status(payment_id)

@app.route('/api/payment', methods=['GET'])
def get_payment_route():
    from pages_py.payment import get_payment_api
    return get_payment_api()

@app.route('/api/payments/all', methods=['GET'])
def get_all_payments_route():
    from pages_py.payment import get_all_payments_api
    return get_all_payments_api()

@app.route('/update_payment/<int:payment_id>', methods=['POST'])
@login_required
def update_payment(payment_id):
    from pages_py.payment import update_payment_info
    return update_payment_info(payment_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Создан пользователь admin с паролем admin")
    app.run(debug=True) 