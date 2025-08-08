#!/bin/bash

# 🚀 Скрипт быстрого деплоя UnifiedSignalBot

echo "🚀 Начинаем деплой UnifiedSignalBot..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker установлен. Перезапустите терминал и запустите скрипт снова."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаем..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Создание директории для логов
mkdir -p logs

# Проверка наличия config.py
if [ ! -f "config.py" ]; then
    echo "❌ Файл config.py не найден!"
    echo "📝 Создайте файл config.py с вашими API ключами (см. README.md)"
    exit 1
fi

echo "✅ Проверки пройдены. Запускаем бота..."

# Остановка существующих контейнеров
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down 2>/dev/null || true

# Удаление старых образов
echo "🧹 Очищаем старые образы..."
docker system prune -f

# Сборка и запуск
echo "🔨 Собираем и запускаем UnifiedSignalBot..."
docker-compose up -d --build

# Проверка статуса
echo "📊 Проверяем статус..."
sleep 5
docker-compose ps

echo "📋 Команды для управления:"
echo "  Просмотр логов: docker-compose logs -f"
echo "  Остановка: docker-compose down"
echo "  Перезапуск: docker-compose restart"
echo "  Статус: docker-compose ps"

echo "🚀 UnifiedSignalBot успешно развернут!"
echo "📱 Отправьте команду /start в Telegram для запуска бота" 