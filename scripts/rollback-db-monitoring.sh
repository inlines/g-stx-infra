#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT"
[[ -f .secrets/preload.before-monitoring ]] || { echo 'Saved pre-monitoring configuration missing.' >&2; exit 1; }
if command -v flock >/dev/null && [[ -d /opt/game-stockx-igdb/sync ]]; then
 exec 9>/opt/game-stockx-igdb/sync/.cron.lock
 flock -n 9 || { echo 'IGDB import is running.' >&2; exit 1; }
fi
rm -f .secrets/db-monitoring.enabled
docker compose --profile db-monitoring stop postgres-metrics
docker compose exec -T postgres psql -X -U postgres -d gstx -v ON_ERROR_STOP=1 -v previous="$(cat .secrets/preload.before-monitoring)" <<'SQL'
SELECT CASE WHEN :'previous' = '' THEN 'ALTER SYSTEM RESET shared_preload_libraries'
 ELSE format('ALTER SYSTEM SET shared_preload_libraries = %L', :'previous') END \gexec
SQL
docker compose restart postgres
ready=false
for attempt in $(seq 1 60); do
 if docker compose exec -T postgres psql -X -U postgres -d gstx -Atc 'SELECT 1' >/dev/null 2>&1; then ready=true; break; fi
 sleep 1
done
[[ "$ready" == true ]] || { echo 'PostgreSQL has not recovered; inspect docker compose logs postgres.' >&2; exit 1; }
echo 'Previous preload list restored. Data, indexes and backups retained. The exporter target will be down until monitoring is enabled again.'
