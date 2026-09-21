#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT"
if command -v flock >/dev/null && [[ -d /opt/game-stockx-igdb/sync ]]; then
 exec 9>/opt/game-stockx-igdb/sync/.cron.lock
 flock -n 9 || { echo 'IGDB import is running; retry after completion.' >&2; exit 1; }
fi
docker compose exec -T postgres psql -X -U postgres -d gstx -v ON_ERROR_STOP=1 < postgres/catalog-indexes.sql
echo 'All five catalog indexes exist, are valid and match expected definitions.'
