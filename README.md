# GSTX Infra

Инфраструктура проекта GSTX: сборка и деплой backend (Rust), frontend (Angular), PostgreSQL, Redis и мониторинга.

## Команды

```bash
docker compose build
docker compose up
docker compose down -v
# g-stx-infra


#all-data-migration.sql нужно положить в /scripts
chmod +x ./data-migration-local.sh
./data-migration-local.sh

chmod +x ./init.sh
./init.sh





# Генерация хеша (выполнить один раз)
echo "basic_auth_users:
  admin: \"$(grep PROMETHEUS_PASSWORD_BCRYPT .env | cut -d= -f2 | tr -d '\"')\"
" > prometheus/web.yml

его же надо явно задать в prometheus/web.yml
+ надо добавить plain в graphana.provisioning/datasources/prometheus.yml