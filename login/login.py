from flask import request, redirect, url_for, render_template, flash
from flask_login import current_user, login_user
from modules.models import User
import logging

logger = logging.getLogger(__name__)

def before_request():
    if not request.endpoint:
        return
    
    logger.info(f"Request path: {request.path}, endpoint: {request.endpoint}")
    
    # Разрешаем доступ к API без авторизации
    if request.path.startswith('/api'):
        logger.info("API request detected, allowing without auth")
        return
    
    # Для всех остальных маршрутов проверяем авторизацию
    if not current_user.is_authenticated and request.endpoint != 'login_router' and request.endpoint != 'static':
        logger.info("Non-API request without auth, redirecting to login")
        return redirect(url_for('login_router'))
    
    logger.info("Request allowed")

def login_function():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')