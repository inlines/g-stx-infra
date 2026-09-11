#!/usr/bin/env bash
# Stage both checkouts before touching the currently buildable sources.
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
MODE=${1:-all}
BRANCH=${2:-main}
case "$MODE" in all|frontend|backend) ;; *) echo 'Usage: init.sh [all|frontend|backend] [branch]' >&2; exit 2 ;; esac
STAGE=$(mktemp -d "${TMPDIR:-/tmp}/gstx-init.XXXXXXXX")
trap 'rm -rf -- "$STAGE"' EXIT
if [[ "$MODE" != backend ]]; then
    git clone --depth 1 --branch "$BRANCH" --single-branch git@github.com:inlines/g-stx-front.git "$STAGE/frontend"
    [[ -f "$STAGE/frontend/package-lock.json" && -d "$STAGE/frontend/src" ]]
fi
if [[ "$MODE" != frontend ]]; then
    git clone --depth 1 --branch "$BRANCH" --single-branch git@github.com:inlines/g-stx-api.git "$STAGE/backend"
    [[ -f "$STAGE/backend/game-stockx-api/Cargo.lock" && -d "$STAGE/backend/game-stockx-api/migrations" ]]
fi
if [[ "$MODE" != backend ]]; then
    for item in angular.json tsconfig.spec.json package-lock.json tsconfig.app.json package.json README.md tsconfig.json public src .nvmrc; do
        rm -rf -- "$ROOT/frontend/$item"
        if [[ -e "$STAGE/frontend/$item" ]]; then cp -R "$STAGE/frontend/$item" "$ROOT/frontend/$item"; fi
    done
    echo 'Frontend sources updated.'
fi
if [[ "$MODE" != frontend ]]; then
    rm -rf -- "$ROOT/backend/game-stockx-api"
    cp -R "$STAGE/backend/game-stockx-api" "$ROOT/backend/game-stockx-api"
    echo 'Backend sources updated.'
fi
find "$ROOT/grafana/provisioning" -type d -exec chmod 755 {} +
find "$ROOT/grafana/provisioning" -type f -exec chmod 644 {} +
