#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_section() {
  local title="$1"
  echo ""
  echo "============================================================"
  echo "$title"
  echo "============================================================"
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: Missing required command: $command_name" >&2
    if [ "$command_name" = "pip-audit" ]; then
      echo "Install it locally with: python -m pip install pip-audit" >&2
    fi
    exit 127
  fi
}

cd "$ROOT_DIR"

require_command "pip-audit"
require_command "npm"

print_section "Python dependency audit: server"
pip-audit -r "$ROOT_DIR/server/requirements.txt"

print_section "Python dependency audit: quizService"
pip-audit -r "$ROOT_DIR/quizService/requirements.txt"

print_section "npm dependency audit: client"
(
  cd "$ROOT_DIR/client"
  npm audit
)
