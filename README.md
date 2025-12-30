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

../ docker compose down && docker compose build && docker compose up



# Генерация хеша (выполнить один раз)
echo "basic_auth_users:
  admin: \"$(grep PROMETHEUS_PASSWORD_BCRYPT .env | cut -d= -f2 | tr -d '\"')\"
" > prometheus/web.yml

его же надо явно задать в prometheus/web.yml
+ надо добавить plain в graphana.provisioning/datasources/prometheus.yml


docker compose stop frontend
docker compose rm frontend
docker compose up -d --force-recreate frontend


docker compose logs -f --tail=all


# Вставь в терминал и нажми Enter
(
  echo "=== ЖИВАЯ СТАТИСТИКА СКАНЕРОВ ==="
  echo ""
  total=0
  docker-compose logs -f frontend 2>&1 | \
    grep --line-buffered -E "(\.php|\.asp)" | \
    while read -r line; do
      total=$((total + 1))
      ip=$(echo "$line" | awk '{print $1}')
      file=$(echo "$line" | awk -F'"' '{print $2}' | awk '{print $2}' | cut -d' ' -f1)
      time_sec=$((total * 28))
      minutes=$((time_sec / 60))
      seconds=$((time_sec % 60))
      printf "\033[32m[+]\033[0m Запрос %d | IP: %s | Файл: %s | Всего времени: %d:%02d\n" \
        "$total" "$ip" "$file" "$minutes" "$seconds"
    done
)