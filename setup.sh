#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

find_python() {
  for candidate in python3.12 python3.13 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      "$candidate" -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))' 2>/dev/null && {
        command -v "$candidate"
        return 0
      }
    fi
  done
  return 1
}

python_exe="$(find_python || true)"
if [[ -z "$python_exe" ]]; then
  echo "Python 3.12 kuruluyor..."
  if command -v brew >/dev/null 2>&1; then
    brew install python@3.12
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  else
    echo "Desteklenen paket yöneticisi bulunamadı. Python 3.11-3.13 kurun." >&2
    exit 1
  fi
  python_exe="$(find_python)"
fi

if [[ ! -x .venv/bin/python ]]; then
  "$python_exe" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip wheel
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.prepare_ocr
touch .venv/.belgeiz-ready
echo "Kurulum tamamlandı. Başlatmak için: ./run.sh"
