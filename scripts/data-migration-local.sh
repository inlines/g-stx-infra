#!/bin/bash

set -e

LOCAL_FILE="~/migrations.sql"
CONTAINER_NAME=$(docker ps --filter "name=postgres" --format "{{.Names}}" | head -n 1)
TARGET_PATH="/tmp/result-data.sql"

if [ -z "$CONTAINER_NAME" ]; then
  echo "❌ PostgreSQL container not found. Is it running?"
  exit 1
fi

if [ ! -f "$LOCAL_FILE" ]; then
  echo "❌ Migration file not found: $LOCAL_FILE"
  exit 1
fi

echo "📦 Copying migration file to $CONTAINER_NAME..."
docker cp "$LOCAL_FILE" "$CONTAINER_NAME":"$TARGET_PATH"

echo "🚀 Running migration inside $CONTAINER_NAME..."
docker exec -e PGPASSWORD="Tn_aQEDvD2" "$CONTAINER_NAME" \
  psql -U postgres -d gstx -f "$TARGET_PATH"

echo "✅ Migration completed."
