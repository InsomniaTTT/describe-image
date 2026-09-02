#!/usr/bin/env bash
# publish.sh — one-command publish of this skill to GitHub.
#
# First run:  creates the GitHub repo (private by default) and pushes.
# Later runs: commits local changes (if any) and pushes.
#
# Requires the GitHub CLI authenticated once:
#   winget install --id GitHub.cli        (Windows)
#   brew install gh                       (macOS)
#   gh auth login                         (then follow the browser prompts)
#
# Make the repo public instead of private:  PUBLIC=1 bash publish.sh

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
REPO_NAME="describe-image"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) not found. Install it first:" >&2
  echo "  Windows: winget install --id GitHub.cli" >&2
  echo "  macOS:   brew install gh" >&2
  echo "  Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md" >&2
  exit 2
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: gh not authenticated. Run:  gh auth login" >&2
  echo "(choose GitHub.com → HTTPS → login with browser, then re-run publish.sh)" >&2
  exit 3
fi

# Commit local changes, if any.
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Committing local changes..."
  git add -A
  git commit -m "Update skill" >/dev/null
  git log --oneline -1
else
  echo "No local changes to commit."
fi

VISIBILITY="--private"
[[ "${PUBLIC:-0}" == "1" ]] && VISIBILITY="--public"

if git remote get-url origin >/dev/null 2>&1; then
  echo "Pushing to existing remote..."
  git push -u "origin" "$BRANCH"
elif gh repo view "$REPO_NAME" >/dev/null 2>&1; then
  echo "GitHub repo already exists — linking it as origin and pushing..."
  USER="$(gh api user -q .login)"
  git remote add origin "https://github.com/$USER/$REPO_NAME.git"
  git push -u origin "$BRANCH"
else
  echo "Creating GitHub repo '$REPO_NAME' ($VISIBILITY) and pushing..."
  gh repo create "$REPO_NAME" $VISIBILITY --source=. --remote=origin --push
fi

USER="$(gh api user -q .login)"
echo
echo "Done. Install on another machine with:"
echo "  git clone https://github.com/$USER/$REPO_NAME.git ~/.zcode/skills/$REPO_NAME"
echo "  (Windows PowerShell: git clone https://github.com/$USER/$REPO_NAME.git \"\$HOME\\.zcode\\skills\\$REPO_NAME\")"