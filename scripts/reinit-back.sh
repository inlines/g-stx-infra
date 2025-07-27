#!/bin/bash

# Проверяем, был ли передан параметр с именем ветки
BRANCH=${1:-main}  # Используем переданный параметр или "main" по умолчанию

# Переход в папку backend
cd ../backend || { echo "Не удалось перейти в папку ../backend"; exit 1; }

# Удаление старых файлов и папок
rm -rf .github g-stx-api game-stockx-api
rm -f requirements.txt README.md
rm -rf game-stockx-api app tests .github g-stx-api game-stockx-api

# Создание целевой папки
mkdir game-stockx-api

# Клонирование репозитория с указанием ветки
echo "Клонируем ветку $BRANCH..."
git clone --branch "$BRANCH" --single-branch git@github.com:inlines/g-stx-api.git || { 
    echo "Ошибка при клонировании backend-репозитория (ветка: $BRANCH)";
    exit 1;
}

# Перенос содержимого
mv g-stx-api/game-stockx-api .
rm -rf g-stx-api

# Настройка прав для Grafana
cd ../grafana
chmod -R 777 provisioning/

echo "Бэкенд готов как с ножа! (Ветка: $BRANCH)"