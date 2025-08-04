# Dockerfile для CryptoAlphaPro Signal Bot v3.0

# Используем Python 3.11 slim образ
FROM python:3.11-slim

# Устанавливаем метаданные
LABEL maintainer="CryptoAlphaPro Team"
LABEL version="3.0"
LABEL description="Professional AI Signal Bot for Cryptocurrency Trading"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt requirements-test.txt ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash cryptoalpha && \
    chown -R cryptoalpha:cryptoalpha /app
USER cryptoalpha

# Создаем директории для логов и данных
RUN mkdir -p /app/logs /app/data

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Открываем порт для API (если понадобится)
EXPOSE 8000

# Создаем health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Команда по умолчанию
CMD ["python", "crypto_signal_bot/full_featured_bot.py"] 