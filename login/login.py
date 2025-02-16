from flask import request, redirect, url_for, render_template, flash
from flask_login import current_user, login_user
from modules.models import User

def before_request():
    if not request.endpoint:
        return
    
    public_endpoints = ['login_router', 'get_promo_route', 'get_bestsales_route', 'static']
    if request.endpoint not in public_endpoints and not current_user.is_authenticated:
        return redirect(url_for('login_router'))

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