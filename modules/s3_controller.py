import os
import requests
from datetime import datetime, timezone
import hashlib
import hmac
import base64
from dotenv import load_dotenv


load_dotenv()

YC_ACCESS_KEY = os.getenv('YC_ACCESS_KEY')
YC_SECRET_KEY = os.getenv('YC_SECRET_KEY')
YC_BUCKET_NAME = os.getenv('YC_BUCKET_NAME')
YC_ENDPOINT_URL = os.getenv('YC_ENDPOINT_URL')

def create_signature(key, date, region, service, string_to_sign):
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    key_date = sign(('AWS4' + key).encode('utf-8'), date)
    key_region = sign(key_date, region)
    key_service = sign(key_region, service)
    key_signing = sign(key_service, 'aws4_request')
    return hmac.new(key_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

def upload_image_to_s3(file_path, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    now = datetime.now(timezone.utc)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')

    region = 'ru-central1'
    service = 's3'
    host = f'{YC_BUCKET_NAME}.{YC_ENDPOINT_URL.replace("https://", "")}'
    endpoint = f'https://{host}/{object_name}'

    with open(file_path, 'rb') as file_data:
        file_content = file_data.read()

    content_sha256 = hashlib.sha256(file_content).hexdigest()

    canonical_request = (
        f"PUT\n/{object_name}\n\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{content_sha256}\n"
        f"x-amz-date:{amz_date}\n"
        f"\nhost;x-amz-content-sha256;x-amz-date\n{content_sha256}"
    )

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )
    signature = create_signature(YC_SECRET_KEY, date_stamp, region, service, string_to_sign)

    headers = {
        'Host': host,
        'x-amz-content-sha256': content_sha256,
        'x-amz-date': amz_date,
        'Authorization': (
            f"{algorithm} Credential={YC_ACCESS_KEY}/{credential_scope}, "
            f"SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature={signature}"
        ),
    }

    try:
        response = requests.put(endpoint, headers=headers, data=file_content)
        if response.status_code == 200:
            print(f"Файл {file_path} успешно загружен в S3 как {object_name}")
            return True
        else:
            print(f"Ошибка при загрузке файла: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False

def delete_image_from_s3(object_name):
    now = datetime.now(timezone.utc)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')

    region = 'ru-central1'
    service = 's3'
    host = f'{YC_BUCKET_NAME}.{YC_ENDPOINT_URL.replace("https://", "")}'
    endpoint = f'https://{host}/{object_name}'

    # Создаем строку для подписи
    content_sha256 = hashlib.sha256(b'').hexdigest()

    canonical_request = (
        f"DELETE\n/{object_name}\n\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{content_sha256}\n"
        f"x-amz-date:{amz_date}\n"
        f"\nhost;x-amz-content-sha256;x-amz-date\n{content_sha256}"
    )

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )
    signature = create_signature(YC_SECRET_KEY, date_stamp, region, service, string_to_sign)

    headers = {
        'Host': host,
        'x-amz-content-sha256': content_sha256,
        'x-amz-date': amz_date,
        'Authorization': (
            f"{algorithm} Credential={YC_ACCESS_KEY}/{credential_scope}, "
            f"SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature={signature}"
        ),
    }

    try:
        response = requests.delete(endpoint, headers=headers)
        if response.status_code in [200, 204]:
            print(f"Файл {object_name} успешно удален из S3")
            return True
        else:
            print(f"Ошибка при удалении файла: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False
