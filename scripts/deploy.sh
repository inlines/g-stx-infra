#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT"
# Coordinate schema migrations with the existing cron wrapper on the VPS.
if command -v flock >/dev/null && [[ -d /opt/game-stockx-igdb/sync ]]; then
  exec 9>/opt/game-stockx-igdb/sync/.cron.lock
  flock -n 9 || { echo 'IGDB import is running; deploy after it finishes.' >&2; exit 1; }
fi
docker compose config --quiet
docker compose build backend frontend
docker compose up -d --no-deps --wait --wait-timeout 180 backend
docker compose up -d --no-deps --force-recreate frontend
docker compose ps backend frontend
