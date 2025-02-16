from flask import render_template, request, jsonify
from modules.models import db, NewProducts
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
import uuid
import os

def new_products_page():
    """Страница управления новинками"""
    products = NewProducts.query.order_by(NewProducts.created_at.desc()).all()
    return render_template('new_products.html', products=products)

def upload_new_product_handler(app):
    """Обработчик загрузки новой новинки"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Нет файла изображения'}), 400
            
        file = request.files['image']
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not all([file, name]):
            return jsonify({'error': 'Все поля должны быть заполнены'}), 400

        # Генерируем уникальный ID
        product_id = str(uuid.uuid4())
        
        # Сохраняем файл временно
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)
        
        # Загружаем файл в S3
        object_name = f"new_products/{product_id}_{file.filename}"
        if upload_image_to_s3(temp_path, object_name):
            # Формируем URL
            s3_url = f"https://{os.getenv('YC_BUCKET_NAME')}.storage.yandexcloud.net/{object_name}"
            
            # Создаем запись в БД
            product = NewProducts(
                id=product_id,
                filename=file.filename,
                name=name,
                description=description,
                s3_url=s3_url
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Удаляем временный файл
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'product': product.to_dict()
            }), 200
        else:
            # Удаляем временный файл в случае ошибки
            os.remove(temp_path)
            return jsonify({'error': 'Ошибка при загрузке файла в S3'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def delete_new_product_handler(product_id):
    """Обработчик удаления новинки"""
    try:
        product = NewProducts.query.get_or_404(product_id)
        
        # Удаляем файл из S3
        object_name = f"new_products/{product.id}_{product.filename}"
        if delete_image_from_s3(object_name):
            # Удаляем запись из БД
            db.session.delete(product)
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Ошибка при удалении файла из S3'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def get_new_products_api():
    """API endpoint для получения списка новинок"""
    try:
        products = NewProducts.query.order_by(NewProducts.created_at.desc()).all()
        return jsonify({
            'success': True,
            'products': [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_new_product_handler(product_id):
    """Обработчик обновления новинки"""
    try:
        product = NewProducts.query.get_or_404(product_id)
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        
        if not name:
            return jsonify({'error': 'Название обязательно'}), 400
            
        product.name = name
        product.description = description
        
        db.session.commit()
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 