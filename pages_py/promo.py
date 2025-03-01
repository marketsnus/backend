from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
import sys
from modules.s3_controller import upload_image_to_s3, delete_image_from_s3
from modules.models import db, Promo
import logging

logger = logging.getLogger(__name__)

def upload_image_handler(app):
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

            new_image = Promo(
                id=file_id,
                filename=filename,
                original_filename=original_filename,
                title=title,
                description=description,
                s3_url=s3_url
            )
            db.session.add(new_image)
            db.session.commit()

            os.remove(temp_path)
            return jsonify(new_image.to_dict()), 200
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': 'Ошибка загрузки в S3'}), 500

    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f'Ошибка при загрузке изображения: {str(e)}')
        return jsonify({'error': str(e)}), 500

def delete_image_handler(image_id):
    try:
        image = Promo.query.get_or_404(image_id)
        if delete_image_from_s3(image.filename):
            db.session.delete(image)
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Ошибка удаления из S3'}), 500
    except Exception as e:
        logger.error(f'Ошибка при удалении изображения {image_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500

def update_image_handler(image_id):
    try:
        image = Promo.query.get_or_404(image_id)
        image.title = request.form.get('title', image.title)
        image.description = request.form.get('description', image.description)
        db.session.commit()
        return jsonify(image.to_dict()), 200
    except Exception as e:
        logger.error(f'Ошибка при обновлении изображения {image_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500