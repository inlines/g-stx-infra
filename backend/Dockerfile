# Стадия сборки
FROM rustlang/rust:nightly AS builder

# Жёстко переопределяем все репозитории на mirror.yandex.ru
RUN echo "deb [trusted=yes] http://mirror.yandex.ru/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://mirror.yandex.ru/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/* && \
    apt-get update -o Acquire::ForceIPv4=true && \
    apt-get install -y postgresql-client libpq-dev pkg-config curl && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем diesel-cli
RUN cargo install diesel_cli@2.2.10 --no-default-features --features postgres

WORKDIR /app
COPY game-stockx-api ./game-stockx-api
WORKDIR /app/game-stockx-api

# Сборка проекта
RUN cargo build --release

# Стадия исполнения
FROM debian:bookworm-slim AS runtime

# Устанавливаем только минимально необходимые пакеты
RUN echo "deb [trusted=yes] http://mirror.yandex.ru/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb [trusted=yes] http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list && \
    rm -f /etc/apt/sources.list.d/* && \
    apt-get update -o Acquire::ForceIPv4=true && \
    apt-get install -y libpq5 postgresql-client-15 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем бинарник и зависимости
COPY --from=builder /app/game-stockx-api/target/release/game-stockx-api ./app
COPY --from=builder /usr/local/cargo/bin/diesel /usr/local/bin/diesel
COPY game-stockx-api/migrations ./migrations
COPY game-stockx-api/diesel.toml ./diesel.toml

# Скрипт миграций
COPY game-stockx-api/migrate.sh /usr/local/bin/migrate.sh
RUN chmod +x /usr/local/bin/migrate.sh

ENTRYPOINT ["/usr/local/bin/migrate.sh"]
CMD ["./app"]
