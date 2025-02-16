from flask import jsonify
from modules.models import db

def get_promo(app, Image):
    with app.app_context():
        images = Image.query.all()
        return jsonify([{
            'id': image.id,
            'filename': image.filename,
            'title': image.title,
            'description': image.description,
            's3_url': image.s3_url
        } for image in images])

def get_bestsales(app, Product):
    with app.app_context():
        products = Product.query.all()
        return jsonify([{
            'id': product.id,
            'filename': product.filename,
            'title': product.name,
            'description': product.category,
            'price': product.price,
            's3_url': product.s3_url
        } for product in products]) 