#!/usr/bin/env bash
# Installs a read-only collector; no database or application restart.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
[[ $(id -u) == 0 ]] || { echo 'Run as root on the VPS.' >&2; exit 1; }
command -v python3 >/dev/null
command -v systemctl >/dev/null
cd "$ROOT"
# Validate everything before installing the recurring job.
python3 -m json.tool grafana/provisioning/dashboards/unknown_serials.json >/dev/null
python3 monitoring/unknown/collect.py
install -d -m 755 /opt/game-stockx-unknown
install -m 644 monitoring/unknown/collect.py monitoring/unknown/counts.sql /opt/game-stockx-unknown/
# A separate config avoids shell interpolation in systemd ExecStart paths.
printf '%s\n' "$ROOT" > /opt/game-stockx-unknown/infra.path
cat > /opt/game-stockx-unknown/run.sh <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
infra=$(cat /opt/game-stockx-unknown/infra.path)
exec /usr/bin/python3 /opt/game-stockx-unknown/collect.py --infra-dir "$infra"
RUN
chmod 755 /opt/game-stockx-unknown/run.sh
cat > /etc/systemd/system/gstx-unknown-metrics.service <<'UNIT'
[Unit]
Description=Game StockX regional Unknown metrics (read-only)
After=docker.service
[Service]
Type=oneshot
ExecStart=/opt/game-stockx-unknown/run.sh
TimeoutStartSec=50
Nice=10
UNIT
cat > /etc/systemd/system/gstx-unknown-metrics.timer <<'UNIT'
[Unit]
Description=Collect Game StockX regional Unknown every five minutes
[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=10s
[Install]
WantedBy=timers.target
UNIT
chmod 644 grafana/provisioning/dashboards/unknown_serials.json
systemctl daemon-reload
systemctl enable --now gstx-unknown-metrics.timer
systemctl start gstx-unknown-metrics.service
# Extend retention while preserving the already-mounted TSDB volume.
# Compose up inherits anonymous volumes. Never use down or --renew-anon-volumes here.
prom_id=$(docker compose ps -q prometheus)
[[ -n "$prom_id" ]] || { echo 'Existing Prometheus container not found; inspect monitoring before proceeding.' >&2; exit 1; }
volume_before=$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/prometheus"}}{{.Source}}{{end}}{{end}}' "$prom_id")
[[ -n "$volume_before" ]] || { echo 'Prometheus data volume not found; refusing recreation.' >&2; exit 1; }
docker compose up -d --no-deps --pull never prometheus
prom_id=$(docker compose ps -q prometheus)
volume_after=$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/prometheus"}}{{.Source}}{{end}}{{end}}' "$prom_id")
[[ "$volume_before" == "$volume_after" ]] || { echo 'Unexpected Prometheus volume change; inspect retained original volume.' >&2; exit 1; }
# Existing textfile mount /var/lib/game-stockx-igdb/metrics and Grafana file provider.
# Start only the textfile exporter if needed; the existing TSDB was preserved above.
docker compose up -d --no-recreate --no-deps igdb-metrics
echo 'Installed. Open Game StockX - Unknown серийники in Grafana after 30-60 seconds.'
echo 'Check: systemctl status gstx-unknown-metrics.timer; journalctl -u gstx-unknown-metrics.service -n 20'
