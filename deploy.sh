#!/bin/bash

set -e

REPO_URL="https://github.com/myachmen/netology-devops-from-zero-homeworks.git"
PROJECT_DIR="/opt/netology-devops-from-zero-homeworks"

echo "=== Установка git ==="
sudo apt update
sudo apt install -y git

echo "=== Клонирование репозитория ==="

if [ -d "$PROJECT_DIR" ]; then
    echo "Каталог уже существует, выполняем обновление"
    cd "$PROJECT_DIR"
    git pull
else
    sudo git clone -b hw-docker-in-practice "$REPO_URL" "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
fi

echo "=== Переход в каталог проекта ==="
cd "$PROJECT_DIR/hw-docker-in-practice"

echo "=== Запуск docker compose ==="
docker compose up -d --build

echo "=== Ожидание запуска сервисов ==="
sleep 15

echo "=== Проверка контейнеров ==="
docker compose ps

echo "=== Проверка приложения ==="
for i in {1..10}; do
    if curl -f http://127.0.0.1:8090; then
        echo
        echo "Application is available"
        break
    fi
    echo "Waiting for application..."
    sleep 5
done

echo "=== Готово ==="