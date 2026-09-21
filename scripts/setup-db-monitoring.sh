#!/usr/bin/env bash
# Explicit one-time operation: may restart PostgreSQL. Never called by deploy.sh.
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT"
if command -v flock >/dev/null && [[ -d /opt/game-stockx-igdb/sync ]]; then
 exec 9>/opt/game-stockx-igdb/sync/.cron.lock
 flock -n 9 || { echo 'IGDB import is running; retry after completion.' >&2; exit 1; }
fi
trap 'echo "Monitoring setup stopped; inspect the error above. Database backups are in $ROOT/.backups. Rollback: bash scripts/rollback-db-monitoring.sh" >&2' ERR
psql_db() { docker compose exec -T postgres psql -X -U postgres -d gstx -v ON_ERROR_STOP=1 "$@"; }
umask 077
mkdir -p .secrets .backups
chmod 700 .secrets .backups
# Pull before touching PostgreSQL, so a network failure cannot interrupt the database.
docker compose --profile db-monitoring pull postgres-metrics
if [[ ! -s .secrets/pg-monitor-password ]]; then openssl rand -hex 32 > .secrets/pg-monitor-password; fi
# The unprivileged exporter reads a single bind-mounted file, not the private host directory.
chmod 644 .secrets/pg-monitor-password
if [[ ! -e .secrets/preload.before-monitoring ]]; then
 psql_db -Atc 'SHOW shared_preload_libraries' > .secrets/preload.before-monitoring
fi
loaded=$(psql_db -Atc "SELECT 'pg_stat_statements'=ANY(string_to_array(replace(current_setting('shared_preload_libraries'),' ',''),','))")
if [[ "$loaded" != t ]]; then
 backup=".backups/before-db-monitoring-$(date +%Y%m%d-%H%M%S).dump"
 docker compose exec -T postgres pg_dump -U postgres -d gstx -Fc > "$backup"
 test -s "$backup"
 docker compose exec -T postgres pg_restore -l < "$backup" > /dev/null
 printf 'Backup: %s/%s\n' "$ROOT" "$backup"
 psql_db <<'SQL'
SELECT format('ALTER SYSTEM SET shared_preload_libraries = %L',concat_ws(',',NULLIF(current_setting('shared_preload_libraries'),''),'pg_stat_statements')) \gexec
SQL
 echo 'Restarting the existing PostgreSQL container to load pg_stat_statements.'
 docker compose restart postgres
fi
ready=false
for attempt in $(seq 1 60); do
 if psql_db -Atc 'SELECT 1' >/dev/null 2>&1; then ready=true; break; fi
 sleep 1
done
[[ "$ready" == true ]] || { echo 'PostgreSQL is not ready. Check logs and rollback instructions.' >&2; exit 1; }
docker compose exec -T -e PG_MONITOR_PASSWORD="$(cat .secrets/pg-monitor-password)" postgres psql -X -U postgres -d gstx -v ON_ERROR_STOP=1 < postgres/monitor-role.sql
psql_db -Atc 'SELECT count(*) FROM pg_stat_statements' >/dev/null
docker compose --profile db-monitoring up -d --no-deps postgres-metrics
ready=false
for attempt in $(seq 1 30); do
 if metrics=$(docker compose --profile db-monitoring exec -T postgres-metrics wget -q -O - -T 10 http://127.0.0.1:9187/metrics 2>/dev/null) &&
    grep -q '^pg_up 1$' <<< "$metrics" &&
    grep -q '^pg_exporter_last_scrape_error 0$' <<< "$metrics" &&
    grep -q '^pg_stat_statements_calls_total{' <<< "$metrics" &&
    ! grep -q '^pg_scrape_collector_success{.*} 0$' <<< "$metrics"; then
  ready=true; break
 fi
 sleep 1
done
[[ "$ready" == true ]] || { echo 'Exporter not ready; check docker compose logs postgres-metrics.' >&2; exit 1; }
# Ordinary deploys preserve the explicitly enabled optional service.
touch .secrets/db-monitoring.enabled
find grafana/provisioning -type d -exec chmod 755 {} +
find grafana/provisioning -type f -exec chmod 644 {} +
# Restart, not recreate, Prometheus: preserve its current writable layer and history.
docker compose restart prometheus
# New provider YAML is read at Grafana startup; its data volume is retained.
docker compose restart grafana
echo 'PostgreSQL monitoring installed. Open Game StockX - PostgreSQL in Grafana; allow 2-5 minutes for rate panels.'
