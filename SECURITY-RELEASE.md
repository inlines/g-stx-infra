# Security release — 2026-09-15

Deploy backend, frontend and infrastructure together. HTTP/IP access is retained.

## Deploy

```sh
cd /root/g-stx-infra
git pull --ff-only
bash scripts/init.sh
python3 scripts/prepare-security-env.py
umask 077
backup="/root/gstx-before-security-$(date +%Y%m%d-%H%M%S).dump"
docker compose exec -T postgres pg_dump -U postgres -d gstx -Fc > "$backup"
test -s "$backup"
bash scripts/deploy.sh
docker compose up -d --no-deps grafana
docker compose ps
docker compose logs --tail=80 backend frontend
```

Run commands in order; stop on any error. Do not use `docker compose down`.
The deploy script waits for the backend health check before replacing the frontend.
The backup is outside the repository. Keep it until verification completes.

The security migration runs automatically on backend startup. Existing tokens retain
validity until password change or expiration. Changing a password invalidates all
old sessions, including chat sockets; the user signs in again. Existing collection
entries and historical prices are preserved. New purchase prices cannot be negative.

The secret preparation script transfers the existing Grafana datasource credential
from the current file or Git history into `.secrets/monitoring.env` with mode 600.
It preserves the value and prints no secrets. If history is missing, it stops before
deployment; restore the existing credential locally, do not invent a new password.
Never commit `.secrets`. This migration does not remove the old secret from Git history;
credential rotation remains a separate coordinated operation.

## Verify

Check login, catalogue, collection, WTS, sending/reading chat messages and admin requests.
Use a test account for password change: old sessions must lose access, new login must work.
Check Grafana datasource connectivity after recreating Grafana. Backend port 9090 is
internal to Docker; public API remains available through frontend nginx.

## Validation and limits

Local: 231 frontend tests, production frontend build, 19 Rust tests, native backend build,
75 HTTP/WebSocket checks through nginx against isolated PostgreSQL/Redis, Compose and
nginx configuration validation. Frontend builds with existing bundle-size warnings.
VPS deployment and Linux image rebuild must still pass on the server.

CSP is report-only to preserve existing UI integrations. HTTPS is excluded by request.
The Rust dependency h2 was removed by disabling unused HTTP/2 on the backend; nginx
uses HTTP/1.1 upstream. The transitive rsa advisory RUSTSEC-2023-0071 remains in the
RustCrypto JWT backend, but the application only uses HS256 and performs no RSA
private-key operations. This is a documented limitation, not a clean dependency audit.
Database role separation and existing index/monitoring experiments are not part of this release.
