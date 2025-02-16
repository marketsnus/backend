from flask import jsonify, request
from werkzeug.utils import secure_filename
import os
import uuid
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3

def upload_promo_image(app, promo_app, Image, promo_db):
    try:
        with promo_app.app_context():
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
                    promo_db.session.add(new_image)
                    promo_db.session.commit()

                    os.remove(temp_path)
                    return jsonify(new_image.to_dict()), 200
                else:
                    os.remove(temp_path)
                    return jsonify({'error': 'Ошибка загрузки в S3'}), 500

            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                promo_db.session.rollback()
                return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def delete_promo_image(promo_app, Image, promo_db, image_id):
    try:
        with promo_app.app_context():
            image = Image.query.get_or_404(image_id)
            if delete_image_from_s3(image.filename):
                promo_db.session.delete(image)
                promo_db.session.commit()
                return jsonify({'success': True}), 200
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
    except Exception as e:
        promo_db.session.rollback()
        return jsonify({'error': str(e)}), 500

def update_promo_image(promo_app, Image, promo_db, image_id):
    try:
        with promo_app.app_context():
            image = Image.query.get_or_404(image_id)
            image.title = request.form.get('title', image.title)
            image.description = request.form.get('description', image.description)
            promo_db.session.commit()
            return jsonify(image.to_dict()), 200
    except Exception as e:
        promo_db.session.rollback()
        return jsonify({'error': str(e)}), 500

def upload_product_image(app, bestsales_app, Product, bestsales_db):
    temp_path = None
    try:
        with bestsales_app.app_context():
            if 'image' not in request.files:
                return jsonify({'error': 'Файл не выбран'}), 400

            file = request.files['image']
            product_id = request.form.get('id', '')
            name = request.form.get('name', '')
            category = request.form.get('category', '')
            price = request.form.get('price', 0)

            if not product_id:
                return jsonify({'error': 'ID товара не указан'}), 400

            if file.filename == '':
                return jsonify({'error': 'Файл не выбран'}), 400

            original_filename = secure_filename(file.filename)
            filename = f"{product_id}_{original_filename}"

            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)

            if upload_image_to_s3(temp_path, filename):
                s3_url = f"https://sqwonkerb.storage.yandexcloud.net/{filename}"

                new_product = Product(
                    id=product_id,
                    name=name,
                    category=category,
                    price=float(price),
                    filename=filename,
                    s3_url=s3_url
                )
                bestsales_db.session.add(new_product)
                bestsales_db.session.commit()

                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify(new_product.to_dict()), 200
            else:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify({'error': 'Ошибка загрузки в S3'}), 500

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        bestsales_db.session.rollback()
        return jsonify({'error': str(e)}), 500

def delete_product_image(bestsales_app, Product, bestsales_db, product_id):
    try:
        with bestsales_app.app_context():
            product = Product.query.get_or_404(product_id)
            if delete_image_from_s3(product.filename):
                bestsales_db.session.delete(product)
                bestsales_db.session.commit()
                return jsonify({'success': True}), 200
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
    except Exception as e:
        bestsales_db.session.rollback()
        return jsonify({'error': str(e)}), 500

def update_product_image(bestsales_app, Product, bestsales_db, product_id):
    try:
        with bestsales_app.app_context():
            product = Product.query.get_or_404(product_id)
            product.name = request.form.get('name', product.name)
            product.category = request.form.get('category', product.category)
            product.price = float(request.form.get('price', product.price))
            bestsales_db.session.commit()
            return jsonify(product.to_dict()), 200
    except Exception as e:
        bestsales_db.session.rollback()
        return jsonify({'error': str(e)}), 500 