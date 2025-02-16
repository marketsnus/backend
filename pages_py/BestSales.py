from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
import sys
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
from modules.models import db, Bestsales

def upload_product_handler(app):
    if 'image' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400

    file = request.files['image']
    name = request.form.get('name', '')
    category = request.form.get('category', '')
    price = request.form.get('price', 0)

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    try:
        product_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{product_id}_{original_filename}"

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        if upload_image_to_s3(temp_path, filename):
            s3_url = f"https://sqwonkerb.storage.yandexcloud.net/{filename}"

            new_product = Bestsales(
                id=product_id,
                filename=filename,
                name=name,
                category=category,
                price=float(price),
                s3_url=s3_url
            )
            db.session.add(new_product)
            db.session.commit()

            os.remove(temp_path)
            return jsonify(new_product.to_dict()), 200
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': 'Ошибка загрузки в S3'}), 500

    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def delete_product_handler(product_id):
    try:
        product = Bestsales.query.get_or_404(product_id)
        if delete_image_from_s3(product.filename):
            db.session.delete(product)
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def update_product_handler(product_id):
    try:
        product = Bestsales.query.get_or_404(product_id)
        product.name = request.form.get('name', product.name)
        product.category = request.form.get('category', product.category)
        product.price = float(request.form.get('price', product.price))
        db.session.commit()
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500