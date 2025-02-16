from flask import Flask, render_template, redirect, url_for, request, jsonify

def get_promo(app, Image):
    try:
        with app.app_context():
            images = Image.query.order_by(Image.created_at.desc()).all()
            return jsonify({
                'success': True,
                'data': [image.to_dict() for image in images]
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_bestsales(app, Product):
    try:
        with app.app_context():
            products = Product.query.order_by(Product.created_at.desc()).all()
            return jsonify({
                'success': True,
                'data': [product.to_dict() for product in products]
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500