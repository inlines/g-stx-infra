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
