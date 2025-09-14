#!/bin/bash

# Скрипт для быстрого запуска системы оптимизации маршрутов

echo "🚚 Система оптимизации маршрутов доставки"
echo "========================================"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю из примера..."
    cp .env.example .env
    echo "📝 Пожалуйста, отредактируйте файл .env и добавьте ваш OpenAI API ключ"
    echo "   nano .env"
    echo ""
    echo "❌ Запуск прерван. Добавьте API ключ и запустите скрипт снова."
    exit 1
fi

# Проверка наличия API ключа
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  API ключ не настроен в файле .env"
    echo "📝 Пожалуйста, отредактируйте файл .env и добавьте ваш OpenAI API ключ"
    echo "   nano .env"
    echo ""
    echo "❌ Запуск прерван. Добавьте API ключ и запустите скрипт снова."
    exit 1
fi

echo "✅ Конфигурация найдена"
echo "🔨 Сборка и запуск Docker контейнеров..."
echo ""

# Запуск системы
docker-compose up --build

echo ""
echo "🎉 Система запущена!"
echo "📱 Frontend: http://localhost:8081"
echo "🔧 Backend API: http://localhost:8001"
echo "🤖 Agent: http://localhost:5000"
echo ""
echo "Для остановки нажмите Ctrl+C или выполните: docker-compose down"
