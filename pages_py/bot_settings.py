from flask import render_template, request, jsonify, current_app
from modules.models import db, BotSettings, BroadcastMessage, BotUser, BroadcastImage
from datetime import datetime
import os
import uuid
from modules.s3_controller import upload_image_to_s3
import asyncio
from bot_handler import send_message, send_media_group, create_bot, get_token
import json
import time
import logging
from aiogram.types import InputMediaPhoto
import requests
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bot_settings_page():
    # Синхронизируем пользователей при каждом открытии страницы
    sync_bot_users()
    
    settings = BotSettings.query.first()
    if not settings:
        settings = BotSettings()
        db.session.add(settings)
        db.session.commit()
    
    broadcasts = BroadcastMessage.query.order_by(BroadcastMessage.created_at.desc()).all()
    
    # Получаем список пользователей
    users = BotUser.query.all()
    
    return render_template('bot_settings.html', settings=settings, broadcasts=broadcasts, users=users)

def update_welcome_message(app):
    try:
        welcome_message = request.form.get('welcome_message')
        if not welcome_message:
            return jsonify({'error': 'Приветственное сообщение не может быть пустым'}), 400
        
        # Проверяем, есть ли загруженное изображение
        image_url = None
        if 'welcome_image' in request.files and request.files['welcome_image'].filename:
            file = request.files['welcome_image']
            
            # Генерируем уникальное имя файла
            original_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"welcome_{uuid.uuid4()}{original_extension}"
            
            # Сохраняем файл локально
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Загружаем файл в S3 и получаем URL
            s3_url = upload_image_to_s3(file_path, unique_filename)
            
            # Удаляем локальный файл после загрузки
            if os.path.exists(file_path):
                os.remove(file_path)
                
            image_url = s3_url
        
        # Обновляем в базе данных
        settings = BotSettings.query.first()
        if not settings:
            settings = BotSettings(welcome_message=welcome_message, welcome_image_url=image_url)
            db.session.add(settings)
        else:
            settings.welcome_message = welcome_message
            if image_url:  # Обновляем изображение только если оно было загружено
                settings.welcome_image_url = image_url
        
        db.session.commit()
        
        # Записываем в файл для бота
        os.makedirs('data', exist_ok=True)
        with open('data/welcome_message.txt', 'w', encoding='utf-8') as file:
            file.write(welcome_message)
            
        # Если было загружено изображение, сохраняем его URL в файл
        if image_url:
            with open('data/welcome_image_url.txt', 'w', encoding='utf-8') as file:
                file.write(image_url)
            
        return jsonify({'success': True, 'message': 'Приветственное сообщение обновлено'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def create_broadcast(app):
    try:
        text = request.form.get('text')
        if not text:
            return jsonify({'error': 'Текст сообщения не может быть пустым'}), 400
        
        # Создаем новую рассылку
        broadcast = BroadcastMessage(
            text=text,
            status='pending'
        )
        
        # Обрабатываем загруженное изображение (только одно)
        if 'image_0' in request.files and request.files['image_0'].filename:
            file = request.files['image_0']
            
            # Генерируем уникальное имя файла
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
                
            # Сохраняем URL изображения
            broadcast.s3_url = s3_url
        
        db.session.add(broadcast)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Рассылка создана'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def send_broadcast(broadcast_id):
    try:
        broadcast = BroadcastMessage.query.get(broadcast_id)
        if not broadcast:
            return jsonify({'error': 'Рассылка не найдена'}), 404
        
        # Синхронизируем пользователей перед отправкой
        sync_bot_users()
        
        # Получаем список активных пользователей
        users = BotUser.query.filter_by(is_active=True).all()
        
        # Счетчик успешно отправленных сообщений
        success_count = 0
        
        # Получаем токен бота из модуля bot_handler.py
        bot_token = get_token()
        
        if not bot_token:
            return jsonify({'error': 'Токен бота не настроен в bot_handler.py'}), 500
        
        # Отправляем сообщение каждому пользователю через HTTP-запросы
        for user in users:
            try:
                chat_id = user.chat_id
                
                # Если есть изображение, отправляем фото с подписью
                if broadcast.s3_url:
                    try:
                        # Получаем изображение
                        image_response = requests.get(broadcast.s3_url, timeout=10)
                        
                        # Отправляем фото с текстом
                        response = requests.post(
                            f'https://api.telegram.org/bot{bot_token}/sendPhoto',
                            params={
                                'chat_id': chat_id,
                                'caption': broadcast.text,
                                'parse_mode': 'HTML'
                            },
                            files={'photo': ('image.jpg', image_response.content, 'image/jpeg')},
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            success_count += 1
                    except Exception as img_err:
                        logger.error(f"Ошибка при отправке изображения: {img_err}")
                        # Если не удалось отправить с изображением, пробуем отправить только текст
                        response = requests.post(
                            f'https://api.telegram.org/bot{bot_token}/sendMessage',
                            json={
                                'chat_id': chat_id,
                                'text': broadcast.text,
                                'parse_mode': 'HTML'
                            },
                            timeout=10
                        )
                        if response.status_code == 200:
                            success_count += 1
                else:
                    # Отправляем только текст
                    response = requests.post(
                        f'https://api.telegram.org/bot{bot_token}/sendMessage',
                        json={
                            'chat_id': chat_id,
                            'text': broadcast.text,
                            'parse_mode': 'HTML'
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        success_count += 1
                
                # Задержка между отправками
                time.sleep(0.3)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user.chat_id}: {e}")
        
        # Обновляем статус рассылки
        broadcast.status = 'sent'
        broadcast.sent_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Рассылка отправлена {success_count} из {len(users)} пользователей'
        })
    except Exception as e:
        logger.error(f"Ошибка при отправке рассылки {broadcast_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def delete_broadcast(broadcast_id):
    try:
        broadcast = BroadcastMessage.query.get(broadcast_id)
        if not broadcast:
            return jsonify({'error': 'Рассылка не найдена'}), 404
        
        # Удаляем все изображения рассылки
        BroadcastImage.query.filter_by(broadcast_id=broadcast_id).delete()
        
        # Удаляем саму рассылку
        db.session.delete(broadcast)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Рассылка успешно удалена'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def sync_bot_users():
    try:
        # Проверяем наличие файла со списком пользователей
        users_list_file = 'data/users/users_list.txt'
        if not os.path.exists(users_list_file):
            return
        
        # Считываем все ID пользователей
        with open(users_list_file, 'r', encoding='utf-8') as f:
            chat_ids = [line.strip() for line in f.readlines() if line.strip()]
        
        # Для каждого ID проверяем наличие файла с данными и импортируем в БД
        for chat_id in chat_ids:
            user_file = f'data/users/{chat_id}.json'
            if not os.path.exists(user_file):
                continue
                
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # Проверяем, существует ли пользователь в БД
            user = BotUser.query.filter_by(chat_id=chat_id).first()
            if not user:
                # Создаем нового пользователя
                user = BotUser(
                    chat_id=chat_id,
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name')
                )
                db.session.add(user)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при синхронизации пользователей: {e}")
        return False

def get_broadcast_images(broadcast_id):
    try:
        # Получаем только изображения для данной рассылки
        broadcast_images = BroadcastImage.query.filter_by(broadcast_id=broadcast_id).all()
        
        # Получаем основное изображение из поля s3_url (для обратной совместимости)
        broadcast = BroadcastMessage.query.get(broadcast_id)
        
        images = []
        
        # Добавляем изображения из таблицы BroadcastImage
        for img in broadcast_images:
            images.append({
                'id': img.id,
                'broadcast_id': img.broadcast_id,
                's3_url': img.s3_url,
                'created_at': img.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Добавляем основное изображение, только если оно есть и его нет в списке
        if broadcast and broadcast.s3_url:
            # Проверяем, что этого URL нет в списке
            if not any(img['s3_url'] == broadcast.s3_url for img in images):
                images.append({
                    'id': None,
                    'broadcast_id': broadcast_id,
                    's3_url': broadcast.s3_url,
                    'created_at': broadcast.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return jsonify({
            'success': True,
            'images': images
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500 