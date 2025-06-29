# Стадия сборки
FROM rustlang/rust:nightly AS builder
ARG BACKEND_REPO

# Устанавливаем зависимости
RUN apt-get update && \
    apt-get install -y postgresql-client libpq-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем diesel-cli
RUN cargo install diesel_cli --no-default-features --features postgres

WORKDIR /app

# Клонируем репозиторий
RUN git clone ${BACKEND_REPO} temp && \
    mv temp/game-stockx-api ./ && \
    rm -rf temp

# Собираем проект
WORKDIR /app/game-stockx-api
RUN cargo build --release

# Стадия исполнения
FROM rustlang/rust:nightly AS runtime

# Устанавливаем зависимости
RUN apt-get update && \
    apt-get install -y postgresql-client libpq-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем diesel-cli (нужен для выполнения миграций)
RUN cargo install diesel_cli --no-default-features --features postgres

# Рабочая директория для рантайма
WORKDIR /app/game-stockx-api

# Копируем бинарник
COPY --from=builder /app/game-stockx-api/target/release/game-stockx-api ./app

# Копируем миграции
COPY --from=builder /app/game-stockx-api/migrations ./migrations

# Копируем скрипт миграций
COPY --from=builder /app/game-stockx-api/migrate.sh /usr/local/bin/migrate.sh
RUN chmod +x /usr/local/bin/migrate.sh

# Переменные окружения
ENV DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@postgres:5432/gstx

# Выполняем миграции и запускаем приложение
ENTRYPOINT ["/usr/local/bin/migrate.sh"]
CMD ["sh", "-c", "until pg_isready -h postgres -p 5432; do sleep 2; done; ./app"]
