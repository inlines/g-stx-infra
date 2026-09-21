# GSTX Infra

Сборка и деплой Angular, Rust, PostgreSQL, Redis и мониторинга.

## Обычный релиз

```sh
cd /root/g-stx-infra
git pull --ff-only
bash scripts/init.sh && bash scripts/deploy.sh
```

`init.sh` обновляет исходники из main. `deploy.sh` собирает приложения, ждёт
готовности backend и пересоздаёт frontend. PostgreSQL и его том не пересоздаются.
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
