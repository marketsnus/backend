from flask import render_template, request, jsonify
from modules.models import db, NewProducts
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
import uuid
import os
import logging
from werkzeug.utils import secure_filename

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def new_products_page():
    """Страница управления новинками"""
    products = NewProducts.query.order_by(NewProducts.created_at.desc()).all()
    return render_template('new_products.html', products=products)

def upload_new_product_handler(app):
    """Обработчик загрузки новой новинки"""
    if 'image' not in request.files:
        logger.warning('Попытка загрузки без файла изображения')
        return jsonify({'error': 'Нет файла изображения'}), 400
        
    file = request.files['image']
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not all([file, name]):
        logger.warning(f'Неполные данные при загрузке: name={name}, file={bool(file)}')
        return jsonify({'error': 'Все поля должны быть заполнены'}), 400

    try:
        product_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        filename = f"{product_id}_{original_filename}"
        logger.info(f'Начало загрузки файла: {filename}')

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        logger.debug(f'Временный файл сохранен: {temp_path}')

        if upload_image_to_s3(temp_path, filename):
            logger.info(f'Файл успешно загружен в S3: {filename}')
            s3_url = f"https://sqwonkerb.storage.yandexcloud.net/{filename}"

            product = NewProducts(
                id=product_id,
                filename=filename,
                name=name,
                description=description,
                s3_url=s3_url
            )
            db.session.add(product)
            db.session.commit()
            logger.info(f'Новая запись добавлена в БД: {product_id}')

            os.remove(temp_path)
            return jsonify(product.to_dict()), 200
        else:
            logger.error(f'Ошибка загрузки файла в S3: {filename}')
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': 'Ошибка загрузки в S3'}), 500

    except Exception as e:
        logger.error(f'Критическая ошибка при создании новинки: {str(e)}', exc_info=True)
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
            logger.debug(f'Временный файл удален: {temp_path}')
        return jsonify({'error': str(e)}), 500

def delete_new_product_handler(product_id):
    """Обработчик удаления новинки"""
    product = NewProducts.query.get_or_404(product_id)
    logger.info(f'Попытка удаления новинки: {product_id}')
    
    if delete_image_from_s3(product.filename):
        logger.info(f'Файл успешно удален из S3: {product.filename}')
        db.session.delete(product)
        db.session.commit()
        logger.info(f'Запись удалена из БД: {product_id}')
        return jsonify({'success': True}), 200
    else:
        logger.error(f'Ошибка удаления файла из S3: {product.filename}')
        return jsonify({'error': 'Ошибка удаления из S3'}), 500

def get_new_products_api():
    """API endpoint для получения списка новинок"""
    logger.info('Запрос списка новинок через API')
    products = NewProducts.query.order_by(NewProducts.created_at.desc()).all()
    return jsonify({
        'success': True,
        'products': [{
            'id': product.id,
            'name': product.name,
            'description': product.description,
            's3_url': product.s3_url,
            'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for product in products]
    }), 200

def update_new_product_handler(product_id):
    """Обработчик обновления новинки"""
    product = NewProducts.query.get_or_404(product_id)
    logger.info(f'Попытка обновления новинки: {product_id}')
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        logger.warning(f'Попытка обновления без названия: {product_id}')
        return jsonify({'error': 'Название обязательно'}), 400
        
    product.name = name
    product.description = description
    
    db.session.commit()
    logger.info(f'Новинка успешно обновлена: {product_id}')
    return jsonify({
        'success': True,
        'product': product.to_dict()
    }), 200 