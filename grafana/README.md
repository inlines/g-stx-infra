# Дашборды Grafana

В репозитории хранятся все три дашборда. Docker Compose монтирует `grafana/provisioning` в Grafana.

| Дашборд | Файл | UID |
| --- | --- | --- |
| GameStockx · Активность и здоровье API | `provisioning/dashboards/api_monitoring.json` | `0926e8e2-6db7-4aa8-9c03-a2b89f4f59b9` |
| Game StockX - PostgreSQL | `provisioning/postgres/postgres_monitoring.json` | `gstx-postgres` |
| Game StockX - Unknown серийники | `provisioning/dashboards/unknown_serials.json` | `gstx-unknown-serials` |

API восстановлен из полного экспорта пользователя 21.09.2026: 61 панель, 64 запроса, 10 смысловых разделов. Сохранены запросы, настройки визуализации и UID. Разделы охватывают API, активность пользователей, модерацию, IGDB и Redis.

Провайдеры находятся в `provisioning/dashboards/api.yml` и `provisioning/dashboards/postgres.yml`. `api.yml` загружает API и Unknown; `postgres.yml` — PostgreSQL.

Обновление на VPS:

```bash
cd /root/g-stx-infra
git pull --ff-only
docker compose restart grafana
```

Тома Grafana и Prometheus удалять не нужно. Эти команды не перезапускают сайт и БД. История метрик хранится в Prometheus, а не в JSON дашбордов.

**Файлы в репозитории являются источником конфигурации.** Grafana позволяет сохранять изменения в интерфейсе, но следующее обновление соответствующего JSON может перезаписать их. После ручных изменений экспортируйте полную актуальную версию в репозиторий. `disableDeletion: true` защищает от удаления при исчезновении файла, но не от перезаписи дашборда с тем же UID.
