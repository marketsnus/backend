from flask import render_template

def promo_page(app, Image):
    with app.app_context():
        images = Image.query.order_by(Image.created_at.desc()).all()
        return render_template('promopage.html', images=images)

def bestsales_page(app, Product):
    with app.app_context():
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('bestsales.html', products=products) 