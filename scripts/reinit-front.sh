#!/usr/bin/env bash
set -euo pipefail
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/init.sh" frontend "${1:-main}"
