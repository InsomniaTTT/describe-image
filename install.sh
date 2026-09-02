#!/usr/bin/env bash
# install.sh — install or update this skill into the ZCode skills directory.
#
# Run from anywhere inside a clone of this repo:
#   bash install.sh [target_dir]
#
# Default target: ~/.zcode/skills/describe-image
# If the target already exists AND is a git clone of this repo, it updates via
# git pull instead of copying (so it stays a real repo for future `git pull`).

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${1:-$HOME/.zcode/skills/describe-image}"

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "Error: SKILL.md not found next to install.sh — run this from inside the repo." >&2
  exit 2
fi

mkdir -p "$(dirname "$DEST")"

if [[ -d "$DEST/.git" ]]; then
  echo "Target exists and is a git repo — updating via git pull..."
  git -C "$DEST" pull --ff-only
elif [[ -e "$DEST" ]]; then
  echo "Error: $DEST already exists and is not a git clone." >&2
  echo "  To replace it: rm -rf \"$DEST\" && bash install.sh" >&2
  exit 3
else
  if git -C "$SRC" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Cloning skill into place (keeps it a git repo for future updates)..."
    git clone "$SRC" "$DEST"
  else
    echo "Copying skill into place..."
    mkdir -p "$DEST/scripts"
    cp "$SRC/SKILL.md" "$DEST/SKILL.md"
    cp "$SRC/scripts/"* "$DEST/scripts/"
  fi
fi

echo
echo "Installed to: $DEST"
echo "Remaining steps:"
echo "  1. Set one vision API key env var (GEMINI_API_KEY / ZHIPU_API_KEY / SILICONFLOW_API_KEY) — see README.md"
echo "  2. Restart ZCode"