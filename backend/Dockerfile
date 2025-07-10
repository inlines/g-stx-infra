# Стадия сборки
FROM rustlang/rust:nightly AS builder

# Устанавливаем зависимости и меняем зеркала
RUN echo "deb http://mirror.yandex.ru/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -o Acquire::ForceIPv4=true update && \
    apt-get install -y postgresql-client libpq-dev pkg-config curl && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем diesel-cli
RUN cargo install diesel_cli --no-default-features --features postgres

WORKDIR /app
COPY game-stockx-api ./game-stockx-api
WORKDIR /app/game-stockx-api

# Сборка проекта
RUN cargo build --release

# Стадия исполнения (рантайм)
FROM debian:bookworm-slim AS runtime

# Устанавливаем зависимости и меняем зеркала
RUN echo "deb http://mirror.yandex.ru/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -o Acquire::ForceIPv4=true update && \
    apt-get install -y postgresql-client libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем бинарник из builder-стадии
COPY --from=builder /app/game-stockx-api/target/release/game-stockx-api ./app

# Копируем diesel CLI
COPY --from=builder /usr/local/cargo/bin/diesel /usr/local/bin/diesel

# Копируем миграции и diesel.toml
COPY game-stockx-api/migrations ./migrations
COPY game-stockx-api/diesel.toml ./diesel.toml

# (опционально) Копируем скрипт миграций
COPY game-stockx-api/migrate.sh /usr/local/bin/migrate.sh
RUN chmod +x /usr/local/bin/migrate.sh

# По умолчанию запускаем скрипт миграции, который потом вызывает бинарник
ENTRYPOINT ["/usr/local/bin/migrate.sh"]
CMD ["./app"]

