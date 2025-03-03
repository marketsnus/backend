from flask import make_response, request

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'  # Временно разрешаем все домены для тестирования
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    
    # Если это preflight запрос, убедимся что он обрабатывается правильно
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Max-Age'] = '3600'
        response.status_code = 200
    return response

def handle_options_request():
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = '*'  # Временно разрешаем все домены для тестирования
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.status_code = 200
    return response 