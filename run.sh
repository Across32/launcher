#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "$(readlink -f -- "$0")")" && pwd)"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "A Launcher még nincs telepítve. Futtasd: bash install.sh" >&2
  exit 1
fi
exec "$ROOT/.venv/bin/python" "$ROOT/launcher.py"
