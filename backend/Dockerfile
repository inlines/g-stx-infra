# Стадия сборки
# Match the working local compiler; floating nightly breaks redis 0.23.x.
FROM rust:1.91.1-bookworm AS builder

# Use the Yandex mirror with Debian signature verification enabled.
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian bookworm main" \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian bookworm-updates main" \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian-security bookworm-security main" \
      > /etc/apt/sources.list && \
    printf '%s\n' 'Acquire::ForceIPv4 "true";' 'Acquire::Retries "2";' \
      'Acquire::http::Timeout "30";' 'Acquire::https::Timeout "30";' \
      > /etc/apt/apt.conf.d/80-build-network

RUN apt-get update --error-on=any && \
    apt-get install -y --no-install-recommends libpq-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем diesel-cli
RUN cargo install diesel_cli@2.2.10 --locked --no-default-features --features postgres

WORKDIR /app
COPY game-stockx-api ./game-stockx-api
WORKDIR /app/game-stockx-api

# Сборка проекта
RUN cargo build --release --locked

# Стадия исполнения
FROM debian:bookworm-slim AS runtime

# Use the Yandex mirror with Debian signature verification enabled.
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf '%s\n' \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian bookworm main" \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian bookworm-updates main" \
      "deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] http://mirror.yandex.ru/debian-security bookworm-security main" \
      > /etc/apt/sources.list && \
    printf '%s\n' 'Acquire::ForceIPv4 "true";' 'Acquire::Retries "2";' \
      'Acquire::http::Timeout "30";' 'Acquire::https::Timeout "30";' \
      > /etc/apt/apt.conf.d/80-build-network

# curl is required by the backend healthcheck in docker-compose.yml.
RUN apt-get update --error-on=any && \
    apt-get install -y --no-install-recommends libpq5 postgresql-client-15 curl ca-certificates && \
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
