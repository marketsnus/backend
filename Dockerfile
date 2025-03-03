FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Делаем скрипт исполняемым
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"] 