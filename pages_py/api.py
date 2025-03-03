from flask import jsonify
from flask_cors import CORS
from modules.models import db
import logging

logger = logging.getLogger(__name__)

def init_api(app):
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:64577", "http://185.224.248.228:5000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

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

def get_bestsales(app, Product):
    with app.app_context():
        products = Product.query.all()
        response = jsonify([{
            'id': product.id,
            'filename': product.filename,
            'title': product.name,
            'description': product.category,
            'price': product.price,
            's3_url': product.s3_url
        } for product in products])
        return response 