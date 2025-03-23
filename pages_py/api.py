from flask import jsonify
from flask_cors import CORS
from modules.models import db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Создаем кеш (если этот файл импортируется отдельно от new_products.py)
_cache = {}
_cache_time = {}

def cached(seconds=60):
    """Декоратор для кеширования результатов функции"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}"
            now = datetime.now()
            
            # Проверяем валидность кеша
            if cache_key in _cache and _cache_time.get(cache_key) > now:
                return _cache[cache_key]
            
            # Получаем и кешируем результат
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_time[cache_key] = now + timedelta(seconds=seconds)
            return result
        return wrapper
    return decorator

def init_api(app):
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:64577", "http://185.224.248.228:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

@cached(seconds=10)
def get_promo(app, Image):
    with app.app_context():
        images = Image.query.all()
        response = jsonify([{
            'id': image.id,
            'filename': image.filename,
            'title': image.title,
            'description': image.description,
            's3_url': image.s3_url
        } for image in images])
        return response

@cached(seconds=10)
def get_bestsales(app, Bestsales):
    """Получение списка товаров из топ продаж"""
    try:
        products = Bestsales.query.all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500 