#!/usr/bin/env bash
# Thin launcher: find a Python interpreter and run describe_image.py with the args.
# (python3 / python / py — order matters; no python3 alias on Windows Git Bash.)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=""
for c in python3 python py; do
  # `command -v` alone is not enough on Windows: the "python3" Microsoft Store
  # app-execution-alias stub exists but isn't a real interpreter. Verify by
  # actually running it.
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
if [[ -z "$PY" ]]; then
  echo "Error: no Python found. Install Python 3 or set it on PATH." >&2
  exit 2
fi
exec "$PY" "$HERE/describe_image.py" "$@"