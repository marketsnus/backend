from flask import render_template, jsonify

def promo_page(promo_app, Image):
    try:
        with promo_app.app_context():
            images = Image.query.order_by(Image.created_at.desc()).all()
        return render_template('index.html', images=images, active_page='promo')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def bestsales_page(bestsales_app, Product):
    try:
        with bestsales_app.app_context():
            products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('products.html', products=products, active_page='bestsales')
    except Exception as e:
        return jsonify({'error': str(e)}), 500 