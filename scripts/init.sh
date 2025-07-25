#!/bin/bash

# Переход в папку frontend
cd ../frontend || { echo "Не удалось перейти в папку ../frontend"; exit 1; }

# Удаление ненужных файлов
rm -f angular.json tsconfig.spec.json package-lock.json tsconfig.app.json package.json README.md tsconfig.json

# Удаление папок
rm -rf g-stx-front public src

# Клонирование репозитория
git clone git@github.com:inlines/g-stx-front.git || { echo "Ошибка при клонировании репозитория"; exit 1; }

# Перемещение содержимого из новой папки
mv g-stx-front/* . || { echo "Не удалось переместить файлы"; exit 1; }

# Удаление пустой папки репозитория
rm -rf g-stx-front

# Установка зависимостей (если нужно)
# npm install

echo "фронт Готов!"


# Переход в папку backend
cd ../backend || { echo "Не удалось перейти в папку ../backend"; exit 1; }

rm -rf .github g-stx-api game-stockx-api

# Удаление старых файлов и папок
rm -f requirements.txt README.md
rm -rf game-stockx-api app tests .github g-stx-api game-stockx-api

mkdir game-stockx-api

# Клонирование репозитория
git clone git@github.com:inlines/g-stx-api.git || { echo "Ошибка при клонировании backend-репозитория"; exit 1; }

mv g-stx-api/game-stockx-api .
rm -rf g-stx-api

cd ../grafana
chmod -R 777 provisioning/


# Установка зависимостей через pip (если нужно)
# pip install -r requirements.txt

echo "Бэкенд готов как с ножа!"

