from flask import request, jsonify, render_template
from modules.models import db, Metadata
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
import os
import uuid
from werkzeug.utils import secure_filename
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Создаем кеш
_cache = {}
_cache_time = {}

def cached(seconds=60):
    """Декоратор для кеширования результатов функции"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}"
            now = datetime.now()
            
            # Проверяем валидность кеша
            if cache_key in _cache and _cache_time.get(cache_key) > now:
                return _cache[cache_key]
            
            # Получаем и кешируем результат
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_time[cache_key] = now + timedelta(seconds=seconds)
            return result
        return wrapper
    return decorator

def get_metadata_value(key, default=''):
    metadata = Metadata.query.filter_by(key=key).first()
    return metadata.value if metadata else default

def upload_category_image(file, category):
    """Загрузка изображения категории в S3"""
    file_id = str(uuid.uuid4())
    original_filename = secure_filename(file.filename)
    filename = f"category_{category}_{file_id}_{original_filename}"
    
    # Временно сохраняем файл
    temp_path = os.path.join('static', 'uploads', filename)
    file.save(temp_path)
    
    # Загружаем в S3
    if upload_image_to_s3(temp_path, filename):
        s3_url = f"https://sqwonkerb.storage.yandexcloud.net/{filename}"
        os.remove(temp_path) 
        return s3_url
    
    os.remove(temp_path)
    raise Exception("Ошибка загрузки файла в S3")

def update_metadata_handler():
    try:
        support_link = request.form.get('support_link', '')
        maintenance_mode = request.form.get('maintenance_mode', 'false')
        
        support = Metadata.query.filter_by(key='support_link').first()
        if not support:
            support = Metadata(key='support_link', value=support_link, description='Ссылка на техподдержку')
            db.session.add(support)
        else:
            support.value = support_link

        # Обновляем статус тех. работ
        maintenance = Metadata.query.filter_by(key='maintenance_mode').first()
        if not maintenance:
            maintenance = Metadata(key='maintenance_mode', value=maintenance_mode, description='Режим технических работ')
            db.session.add(maintenance)
        else:
            maintenance.value = maintenance_mode

        # Обновляем картинки категорий
        categories = ['snus', 'disposable', 'liquids', 'pod_systems', 'accessories']
        for category in categories:
            if category in request.files:
                file = request.files[category]
                if file and file.filename:
                    try:
                        s3_url = upload_category_image(file, category)
                        
                        old_metadata = Metadata.query.filter_by(key=f'category_image_{category}').first()
                        if old_metadata and old_metadata.value:
                            old_filename = old_metadata.value.split('/')[-1]
                            delete_image_from_s3(old_filename)
                        
                        if not old_metadata:
                            metadata = Metadata(
                                key=f'category_image_{category}',
                                value=s3_url,
                                description=f'Изображение для категории {category}'
                            )
                            db.session.add(metadata)
                        else:
                            old_metadata.value = s3_url
                    except Exception as e:
                        return jsonify({'error': f'Ошибка загрузки изображения для категории {category}: {str(e)}'}), 500

        db.session.commit()
        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f'Ошибка при обновлении метаданных: {str(e)}')
        return jsonify({'error': str(e)}), 500

def delete_category_image(category):
    """Удаление изображения категории"""
    try:
        metadata = Metadata.query.filter_by(key=f'category_image_{category}').first()
        if metadata and metadata.value:
            filename = metadata.value.split('/')[-1]
            if delete_image_from_s3(filename):
                metadata.value = ''
                db.session.commit()
                return jsonify({'success': True}), 200
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
        return jsonify({'error': 'Изображение не найдено'}), 404
    except Exception as e:
        logger.error(f'Ошибка при удалении изображения категории {category}: {str(e)}')
        return jsonify({'error': str(e)}), 500

def get_map_data():
    """Получение Map данных из БД"""
    metadata = Metadata.query.filter_by(key='map_data').first()
    if metadata and metadata.value:
        try:
            # Парсим JSON для проверки валидности и сразу возвращаем его
            return json.loads(metadata.value)
        except json.JSONDecodeError:
            return ''
    return ''

def save_map_data(json_data):
    """Сохранение Map данных в БД"""
    metadata = Metadata.query.filter_by(key='map_data').first()
    if metadata:
        metadata.value = json_data
    else:
        metadata = Metadata(
            key='map_data',
            value=json_data,
            description='Map данные'
        )
        db.session.add(metadata)
    db.session.commit()

def metadata_page():
    metadata = {
        'support_link': get_metadata_value('support_link'),
        'maintenance_mode': get_metadata_value('maintenance_mode', 'false'),
        'map_data': get_map_data(),
        'category_images': {
            'snus': get_metadata_value('category_image_snus'),
            'disposable': get_metadata_value('category_image_disposable'),
            'liquids': get_metadata_value('category_image_liquids'),
            'pod_systems': get_metadata_value('category_image_pod_systems'),
            'accessories': get_metadata_value('category_image_accessories')
        }
    }
    return render_template('metadata.html', metadata=metadata)

@cached(seconds=30)  # Более длительное кеширование для метаданных
def get_metadata_api():
    """API для получения метаданных"""
    try:
        metadata = {
            'support_link': get_metadata_value('support_link'),
            'maintenance_mode': get_metadata_value('maintenance_mode', 'false') == 'true',
            'map_data': get_map_data(),
            'category_images': {
                'snus': get_metadata_value('category_image_snus'),
                'disposable': get_metadata_value('category_image_disposable'),
                'liquids': get_metadata_value('category_image_liquids'),
                'pod_systems': get_metadata_value('category_image_pod_systems'),
                'accessories': get_metadata_value('category_image_accessories')
            }
        }
        return jsonify(metadata), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def import_json_metadata():
    try:
        json_data = request.form.get('json_data')
        if not json_data:
            return jsonify({'error': 'Данные не предоставлены'}), 400

        # Проверяем валидность JSON
        try:
            json.loads(json_data)
        except json.JSONDecodeError:
            return jsonify({'error': 'Неверный формат данных'}), 400

        # Сохраняем map данные
        save_map_data(json_data)
        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f'Ошибка при импорте Map данных: {str(e)}')
        return jsonify({'error': str(e)}), 500