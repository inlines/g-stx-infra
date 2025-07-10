#!/bin/bash

# Переход в папку frontend
cd ../frontend

# Удаление ненужных файлов
rm angular.json tsconfig.spec.json package-lock.json tsconfig.app.json package.json README.md tsconfig.json

# Удаление папок
rm -rf g-stx-front public src
