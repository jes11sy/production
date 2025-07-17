FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY config/alembic.ini ./alembic.ini
COPY run.py .

# Создание необходимых папок
RUN mkdir -p logs media

# Выставление портов
EXPOSE 8000

# Команда запуска
CMD ["python", "run.py"] 