#!/usr/bin/env bash
# Chạy lệnh Python trong myvenv (tạo venv nếu chưa có).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV="${ROOT}/myvenv"

if [[ ! -d "$VENV/bin" ]]; then
  echo "Tạo virtualenv tại $VENV ..."
  if ! python3 -m venv "$VENV" 2>/dev/null; then
    echo "Lỗi: cần cài python3-venv — sudo apt install python3-venv python3-pip"
    exit 1
  fi
  "$VENV/bin/pip" install -r requirements.txt
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"
exec "$@"
