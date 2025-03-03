#!/bin/sh

# Создаем базу данных и таблицы
python -c "
from admin import app, db, User
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print('Created admin user')
"

# Запускаем приложение
exec python admin.py 