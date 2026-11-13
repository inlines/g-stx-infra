# GSTX Infra

Сборка и деплой Angular, Rust, PostgreSQL, Redis и мониторинга.

## Обычный релиз

```sh
cd /root/g-stx-infra
git pull --ff-only
bash scripts/init.sh && bash scripts/deploy.sh
```

`init.sh` обновляет исходники из main. `deploy.sh` собирает приложения, запускает
PostgreSQL и Redis и ждёт их готовности перед запуском backend. Затем ждёт
готовности backend и пересоздаёт frontend. Отсутствующие контейнеры зависимостей
создаются заново; существующий том PostgreSQL сохраняется.
Исправление Nginx исключает штатный IPv6 helper, зависавший на `apk manifest nginx`;
слушатели задаются нашим `frontend/nginx.conf`.

## Индексы и мониторинг PostgreSQL — установка один раз

Выполнять после `git pull`, в период небольшой нагрузки. Скрипты согласуют работу
с блокировкой IGDB cron. Не запускайте одновременно другие миграции.

```sh
cd /root/g-stx-infra
bash scripts/db-indexes.sh
bash scripts/setup-db-monitoring.sh
```

Первый скрипт создаёт пять неуникальных B-tree индексов `CONCURRENTLY` для
screenshots, involved_companies, game_franschises. Строки и серийники не изменяются.
Он проверяет определения и валидность индексов до и после создания; повторный запуск
безопасен. При прерывании concurrent-создания может остаться INVALID индекс:
скрипт остановится, такой индекс нужно отдельно проверить перед удалением/повтором.

Второй скрипт сначала скачивает exporter, сохраняет прежний shared_preload_libraries,
перед первым перезапуском создаёт дамп в `.backups` и проверяет его оглавление.
Добавляет pg_stat_statements с сохранением других библиотек и один раз перезапускает
существующий PostgreSQL. В этот короткий период API может отвечать ошибкой;
после готовности БД пул соединений должен восстановиться. Повторная установка
не перезапускает уже настроенную БД.

Пароль отдельной роли `gstx_monitor` хранится в `.secrets/pg-monitor-password`.
Роль не суперпользователь, имеет pg_monitor и read-only по умолчанию. Exporter
доступен только в Docker-сети, без внешнего порта; текст SQL не экспортируется.
После успешной проверки сохраняется `.secrets/db-monitoring.enabled` — обычный
деплой запускает включённый exporter. Не удалять `.secrets`, `.backups` и Docker-тома.

Prometheus перезапускается **без пересоздания**, сохраняя текущий том истории.
Grafana также перезапускается без пересоздания, чтобы прочитать новый provider, и подхватит **Game StockX - PostgreSQL** в течение 30 секунд. Rate-панелям
нужно несколько сборов метрик. Среднее SQL-время не является p95 HTTP-запроса.
SQL-панели исключают роль мониторинга, но включают backend и импорты.

Проверки на VPS:

```sh
docker compose exec -T postgres psql -X -U postgres -d gstx -c 'SELECT count(*) FROM pg_stat_statements;'
docker compose --profile db-monitoring logs --tail=20 postgres-metrics
docker compose exec -T backend curl -fsS http://127.0.0.1:9090/health
curl -I --max-time 10 http://127.0.0.1/
```

В Grafana: PostgreSQL доступен = 1, ошибка сбора = 0. В Prometheus `up{job="postgres"}`
и `pg_up{job="postgres"}` должны быть 1. Все `pg_scrape_collector_success` — 1.

Откат мониторинга (с ещё одним коротким перезапуском PostgreSQL):

```sh
bash scripts/rollback-db-monitoring.sh
```

Скрипт останавливает exporter, снимает маркер включения, восстанавливает прежний
список preload и ждёт готовности БД. Данные, индексы, расширение и дампы сохраняются;
метрики postgres после отката недоступны. Дамп автоматически не восстанавливается.

Для анализа тяжёлого SQL по queryid из Grafana (вывод содержит SQL, не публиковать):

```sql
SELECT queryid, calls, total_exec_time, mean_exec_time, query
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'gstx')
ORDER BY total_exec_time DESC LIMIT 10;
```

## Безопасность данных

Не использовать `docker compose down -v` на боевом сервере: он удаляет именованные
тома, включая PostgreSQL. Файлы конфигурации, секреты и резервные копии хранятся
внутри каталога инфры; обложки находятся в `/var/www/static`.

## Постоянная история Prometheus

Prometheus хранит TSDB в `/prometheus/data` на внешнем именованном томе
`g-stx-infra_prometheus-data`. Он сохраняется при пересоздании контейнера и
`docker compose down -v`; явное удаление тома всё равно уничтожит данные.
Политика хранения остаётся прежней: 90 дней или 2 ГБ (какой лимит сработает раньше).

Для существующего VPS после обновления репозитория, до `compose up`:

```sh
python3 scripts/migrate-prometheus-storage.py && docker compose up -d --no-deps --pull never prometheus
```

Скрипт требует root на Docker-хосте. Он останавливает только Prometheus,
копирует весь старый том с сохранением владельцев, проверяет SHA-256 каждого файла
и оставляет оригинал. После успешного копирования Prometheus остаётся остановленным
до команды `compose up`. При ошибке копирования исходный контейнер запускается снова.
Непустой неподключённый целевой том не перезаписывается; требуется проверка вручную.
Если целевой том уже подключён, повторный запуск ничего не копирует.

На новой установке без истории сначала выполните:

```sh
docker volume create g-stx-infra_prometheus-data
```

Исходный анонимный том не удаляйте до проверки графиков и резервной копии.

## Восстановление после перезагрузки VPS

Все постоянные сервисы используют `restart: unless-stopped`: Docker запускает
существующие контейнеры после перезагрузки хоста и перезапускает завершившиеся
процессы. Включите Docker при загрузке ОС: `systemctl enable docker.service`.
Контейнеры, вручную остановленные через `stop`, остаются остановленными; удалённые
через `down` нужно создать командой `compose up`.

Применение конфигурации к существующей установке с готовыми образами:

```sh
cd /root/g-stx-infra && git pull --ff-only && systemctl enable docker.service && docker compose up -d --no-build --pull never --wait --wait-timeout 180
```

Команда может кратковременно перезапустить изменённые сервисы. Именованные тома
сохраняются. Для PostgreSQL предусмотрено до 60 секунд на штатную остановку.
При `compose up` backend ждёт готовности PostgreSQL и Redis, frontend — backend.
При загрузке Docker порядок `depends_on` не применяется: backend использует
своё ожидание PostgreSQL, завершившиеся процессы повторно запускает Docker.
Статус `unhealthy` сам по себе не вызывает перезапуск контейнера.

Проверка после перезагрузки:

```sh
docker compose ps
docker compose exec -T backend curl -fsS http://127.0.0.1:9090/health
curl -I --max-time 10 http://127.0.0.1/
```
