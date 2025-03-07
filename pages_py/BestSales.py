from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
import sys
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
from modules.models import db, Bestsales
import logging

logger = logging.getLogger(__name__)

def upload_bestsale_handler(app):
    """Обработчик загрузки товара в топ продаж"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Нет файла изображения'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400

        # Получаем данные из формы
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        product_id = request.form.get('id')

        if not all([name, category, price, product_id]):
            return jsonify({'error': 'Не все поля заполнены'}), 400

        # Генерируем уникальное имя файла, сохраняя расширение оригинального файла
        original_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{original_extension}"
        
        # Сохраняем файл локально
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Загружаем файл в S3 и получаем URL
        s3_url = upload_image_to_s3(file_path, unique_filename)
        
        # Удаляем локальный файл после загрузки
        if os.path.exists(file_path):
            os.remove(file_path)
            
        if not s3_url:
            return jsonify({'error': 'Ошибка при загрузке файла в S3'}), 500

        # Создаем новый объект Bestsales
        new_product = Bestsales(
            id=product_id,
            name=name,
            category=category,
            price=price,
            filename=unique_filename,
            s3_url=s3_url
        )

        db.session.add(new_product)
        db.session.commit()
        logger.info(f"Товар {product_id} успешно добавлен в базу данных")

        return jsonify({'message': 'Товар успешно добавлен', 'id': new_product.id}), 200

    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {str(e)}")
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
        logger.error(f'Ошибка при удалении товара {product_id}: {str(e)}')
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
        logger.error(f'Ошибка при обновлении товара {product_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500